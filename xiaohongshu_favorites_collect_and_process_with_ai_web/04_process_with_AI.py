import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from client_sdk.params import TaskParams
from client_sdk.rpc_client import EAIRPCClient  # type: ignore
from utils.file_utils import read_json_with_project_root, write_json_with_project_root, PROJECT_ROOT

# ----------------------
# Config
# ----------------------
INPUT_NORMALIZED_PATH = "data/favorite_notes_normalized.json"
OUTPUT_AI_RESULT_PATH = "data/favorite_notes_ai_processed.json"
FAIL_LOG_PATH = "data/favorite_notes_ai_failures.json"

# 控制是否重处理已完成的笔记，以及是否对部分完成的笔记继续补齐剩余任务
REPROCESS_EXISTING = False
RESUME_PARTIAL = True

# RPC client config
RPC_BASE_URL = "http://127.0.0.1:8008"
RPC_API_KEY = "testkey"
RPC_WEBHOOK_HOST = "127.0.0.1"
RPC_WEBHOOK_PORT = 0

# Yuanbao chat params
COOKIE_IDS = [
    "819969a2-9e59-46f5-b0ca-df2116d9c2a0"
]
CONV_ID = "3df6b8e0-5ddc-444a-be11-a866b8342a39"

# 每5s进入下一个笔记
AI_INTERVAL_SEC = 5

# ----------------------
# Utilities
# ----------------------

def _clean_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return s.replace("\n", "")


def _join_tags(tags: Optional[List[str]]) -> str:
    if not tags:
        return ""
    seen = set()
    cleaned: List[str] = []
    for t in tags:
        if not t:
            continue
        k = str(t).strip()
        if not k:
            continue
        low = k.lower()
        if low in seen:
            continue
        seen.add(low)
        cleaned.append(k)
    return ", ".join(cleaned)


def _json_try_loads(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        return None


def _extract_json_from_text(text: str) -> Optional[dict]:
    if not text:
        return None
    # Remove code fences if any
    text2 = re.sub(r"```(json)?", "", text, flags=re.IGNORECASE).strip()
    data = _json_try_loads(text2)
    if data is not None:
        return data
    # Try to find first {...} block
    start = text2.find("{")
    end = text2.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = text2[start : end + 1]
        return _json_try_loads(chunk)
    return None

# ----------------------
# Prompts
# ----------------------

def build_prompt_summary(title: str, desc: str, tags_joined: str) -> str:
    return (
        "你是内容摘要助手。给定【标题】【正文】【标签】："
        "- 若正文充分，以正文为主。"
        "- 若正文稀缺，仅基于标题与标签；禁止虚构细节。"
        "- 摘要≤200字。输出JSON：{\"summary_200\":\"...\", \"confidence\":0~1}"
        f"【标题】{title}"
        f"【正文】{desc}"
        f"【标签】{tags_joined}"
    )


def build_prompt_keywords(title: str, content_for_keywords: str) -> str:
    return (
        "基于给定内容，提取3-5个名词类关键词（专有名词优先）。输出JSON："
        '{"keywords":["...","..."], "confidence":0~1}'
        "内容："
        f"{title}{content_for_keywords}"
    )


def build_prompt_topics(title: str, desc: str, tags_joined: str) -> str:
    return (
        "从内容中判定 primary_topic、subtopics、content_intent、content_type。"
        "必须从给定词表中选择，输出JSON（多余字段不要）："
        '{"primary_topic":"…","subtopics":["…"],"content_intent":"…","content_type":"…","confidence":0~1}'
        "词表："
        "primary_topic: [AI工具, 穿搭, 旅行, 健身, 理财, 摄影, 美食, 教育, 职场, 心理, 家居, 亲子, 宠物, 影视, 游戏, 科技]"
        "content_intent: [教程, 经验分享, 测评, 种草, 记录, 新闻, 活动, 招聘, 广告]"
        "content_type: [图文, 长文, 短视频, 教程清单, 测评对比, 随笔]"
        "内容："
        f"{title}{desc}{tags_joined}"
    )


# ----------------------
# Persistence helpers (immediate write, resumable)
# ----------------------

def _load_processed_state() -> Dict[str, Any]:
    try:
        state = read_json_with_project_root(OUTPUT_AI_RESULT_PATH)
        if isinstance(state, dict):
            # 兼容旧结构：确保 data 为 list
            if not isinstance(state.get("data"), list):
                state["data"] = []
            return state
    except FileNotFoundError:
        pass
    return {
        "platform": None,
        "source": INPUT_NORMALIZED_PATH,
        "tasks": [],
        "count": 0,
        "data": [],
    }


def _save_processed_state(state: Dict[str, Any]) -> None:
    # 重新计算 count
    state["count"] = len(state.get("data", []))
    write_json_with_project_root(OUTPUT_AI_RESULT_PATH, state)


def _append_failure_log(record: Dict[str, Any]) -> None:
    try:
        existing = read_json_with_project_root(FAIL_LOG_PATH)
        if not isinstance(existing, list):
            existing = []
    except FileNotFoundError:
        existing = []
    existing.append(record)
    write_json_with_project_root(FAIL_LOG_PATH, existing)


def _index_by_note_id(state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for item in state.get("data", []):
        nid = item.get("note_id")
        if isinstance(nid, str) and nid:
            index[nid] = item
    return index


def _merge_note_result_into_state(state: Dict[str, Any], note_result: Dict[str, Any]) -> None:
    # 如存在相同 note_id 则替换，否则追加
    note_id = note_result.get("note_id")
    assert isinstance(note_id, str) and note_id
    replaced = False
    for i, item in enumerate(state.get("data", [])):
        if item.get("note_id") == note_id:
            state["data"][i] = note_result
            replaced = True
            break
    if not replaced:
        state.setdefault("data", []).append(note_result)


# ----------------------
# Task Abstractions
# ----------------------

class Task:
    name: str

    def prompt(self, normalized: dict) -> str:
        raise NotImplementedError

    def parse_and_validate(self, model_text: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def run(self, client: EAIRPCClient, normalized: dict) -> Dict[str, Any]:
        p = self.prompt(normalized)
        try:
            chat_result = await client.chat_with_yuanbao(
                ask_question=p,
                conversation_id=CONV_ID,
                task_params=TaskParams(
                    cookie_ids=COOKIE_IDS,
                    close_page_when_task_finished=True,
                ),
            )
            data = chat_result.get("data") if isinstance(chat_result, dict) else None
            if not (isinstance(data, list) and data and isinstance(data[0], dict)):
                raise RuntimeError("unexpected AI response shape")
            text = data[0].get("last_model_message")
            if not isinstance(text, str) or not text.strip():
                raise RuntimeError("empty model message")
            parsed = self.parse_and_validate(text)
            return {"ok": True, "result": parsed, "raw": text}
        except Exception as e:
            err = {"type": type(e).__name__, "message": str(e)}
            # 若能拿到原始文本，尝试附带截断信息
            raw = None
            try:
                raw = locals().get("text")  # type: ignore
            except Exception:
                raw = None
            return {"ok": False, "error": err, "raw": raw, "prompt_excerpt": p}


class SummaryTask(Task):
    name = "summary"

    def prompt(self, normalized: dict) -> str:
        title = _clean_text((normalized or {}).get("title"))
        desc = _clean_text((normalized or {}).get("desc"))
        tags_joined = _join_tags((normalized or {}).get("tags") or [])
        return build_prompt_summary(title, desc, tags_joined)

    def parse_and_validate(self, model_text: str) -> Dict[str, Any]:
        data = _extract_json_from_text(model_text)
        if not isinstance(data, dict):
            raise ValueError("summary: invalid JSON")
        if "summary_200" not in data or not isinstance(data["summary_200"], str):
            raise ValueError("summary: missing summary_200")
        # confidence 可选
        return {"summary_200": data["summary_200"], "confidence": data.get("confidence")}


class KeywordsTask(Task):
    name = "keywords"

    def prompt(self, normalized: dict) -> str:
        title = _clean_text((normalized or {}).get("title"))
        desc = _clean_text((normalized or {}).get("desc"))
        tags = (normalized or {}).get("tags") or []
        # 当正文不足时，关键词提取可强调标题/标签
        content_for_keywords = desc if desc else (title + "" + _join_tags(tags))
        return build_prompt_keywords(title, content_for_keywords)

    def parse_and_validate(self, model_text: str) -> Dict[str, Any]:
        data = _extract_json_from_text(model_text)
        if not isinstance(data, dict):
            raise ValueError("keywords: invalid JSON")
        kws = data.get("keywords")
        if not isinstance(kws, list) or not all(isinstance(x, str) for x in kws):
            raise ValueError("keywords: missing or invalid keywords array")
        return {"keywords": kws, "confidence": data.get("confidence")}


class TopicsTask(Task):
    name = "topics"

    ALLOWED_PRIMARY = ["AI工具", "穿搭", "旅行", "健身", "理财", "摄影", "美食", "教育", "职场", "心理", "家居", "亲子", "宠物", "影视", "游戏", "科技"]
    ALLOWED_INTENT = ["教程", "经验分享", "测评", "种草", "记录", "新闻", "活动", "招聘", "广告"]
    ALLOWED_TYPE = ["图文", "长文", "短视频", "教程清单", "测评对比", "随笔"]

    def prompt(self, normalized: dict) -> str:
        title = _clean_text((normalized or {}).get("title"))
        desc = _clean_text((normalized or {}).get("desc"))
        tags_joined = _join_tags((normalized or {}).get("tags") or [])
        return build_prompt_topics(title, desc, tags_joined)

    def parse_and_validate(self, model_text: str) -> Dict[str, Any]:
        data = _extract_json_from_text(model_text)
        if not isinstance(data, dict):
            raise ValueError("topics: invalid JSON")
        required = ["primary_topic", "subtopics", "content_intent", "content_type"]
        for k in required:
            if k not in data:
                raise ValueError(f"topics: missing {k}")
        if data["primary_topic"] not in self.ALLOWED_PRIMARY:
            raise ValueError("topics: primary_topic not in allowed list")
        if not isinstance(data["subtopics"], list) or not all(isinstance(x, str) for x in data["subtopics"]):
            raise ValueError("topics: subtopics must be list[str]")
        if data["content_intent"] not in self.ALLOWED_INTENT:
            raise ValueError("topics: content_intent not in allowed list")
        if data["content_type"] not in self.ALLOWED_TYPE:
            raise ValueError("topics: content_type not in allowed list")
        return {
            "primary_topic": data["primary_topic"],
            "subtopics": data["subtopics"],
            "content_intent": data["content_intent"],
            "content_type": data["content_type"],
            "confidence": data.get("confidence"),
        }


# Registry of tasks (extensible)
TASKS: List[Task] = [SummaryTask(), KeywordsTask(), TopicsTask()]


# ----------------------
# Per-note processing and immediate persistence
# ----------------------

async def process_one_note(client: EAIRPCClient, normalized_item: dict, existing: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    norm = normalized_item.get("normalized", {}) if isinstance(normalized_item, dict) else {}
    note_id = norm.get("note_id") or normalized_item.get("id") or ""

    # 初始化/承接已存在的结果（用于断点续跑，仅补未完成任务）
    note_result: Dict[str, Any] = existing.copy() if isinstance(existing, dict) else {"note_id": note_id, "tasks": {}}

    # 逐任务执行；若已有该任务且 ok 且不重跑，则跳过
    for task in TASKS:
        task_state = (note_result.get("tasks") or {}).get(task.name)
        if task_state and task_state.get("ok") and not REPROCESS_EXISTING:
            continue
        # 运行任务
        res = await task.run(client, norm)
        # 写入任务结果
        note_result.setdefault("tasks", {})[task.name] = res
        # 失败则写一条失败日志（但不中断其他任务）
        if not res.get("ok"):
            _append_failure_log({
                "note_id": note_id,
                "task": task.name,
                "error": res.get("error"),
                "raw_response_excerpt": res.get("raw"),
                "prompt_excerpt": res.get("prompt_excerpt"),
            })

    # 汇总状态
    task_values = list((note_result.get("tasks") or {}).values())
    oks = [t for t in task_values if t.get("ok")]
    if len(oks) == len(task_values) and task_values:
        status = "ok"
    elif any(t.get("ok") for t in task_values):
        status = "partial"
    else:
        status = "failed"
    note_result["status"] = status

    # 兼容：拍平成功任务（summary/keywords/topics）以兼容后续可能的消费端
    if note_result["tasks"].get("summary", {}).get("ok"):
        note_result["summary"] = note_result["tasks"]["summary"]["result"]
    if note_result["tasks"].get("keywords", {}).get("ok"):
        note_result["keywords"] = note_result["tasks"]["keywords"]["result"]
    if note_result["tasks"].get("topics", {}).get("ok"):
        note_result["topics"] = note_result["tasks"]["topics"]["result"]

    return note_result


# ----------------------
# Main
# ----------------------

async def main():
    print("🚀 AI处理阶段启动：读取规范化数据，执行任务并即时落盘（可恢复）")

    norm_payload = read_json_with_project_root(INPUT_NORMALIZED_PATH)
    items: List[dict] = norm_payload.get("data") if isinstance(norm_payload, dict) else None
    if not isinstance(items, list):
        raise RuntimeError("规范化输入数据格式不正确：应包含 data 数组")

    # 载入当前处理状态
    state = _load_processed_state()
    # 首次运行时补充元信息
    if state.get("platform") is None:
        state["platform"] = norm_payload.get("platform", "xhs")
        state["source"] = INPUT_NORMALIZED_PATH
    state["tasks"] = [t.name for t in TASKS]

    index = _index_by_note_id(state)

    client = EAIRPCClient(
        base_url=RPC_BASE_URL,
        api_key=RPC_API_KEY,
        webhook_host=RPC_WEBHOOK_HOST,
        webhook_port=RPC_WEBHOOK_PORT,
    )

    try:
        await client.start()
        print("✅ RPC客户端已启动")

        for idx, item in enumerate(items, start=1):
            note_id = (item.get("normalized") or {}).get("note_id") or item.get("id") or ""
            if not note_id:
                print(f"⚠️ 跳过无效笔记（缺少 note_id）: index={idx}")
                continue

            existing = index.get(note_id)
            # 判断是否需要处理（已完成且不重跑 -> 跳过；部分完成且允许续跑 -> 处理剩余）
            if existing:
                if existing.get("status") == "ok" and not REPROCESS_EXISTING:
                    print(f"⏭️ 跳过已完成笔记: {note_id}")
                    continue
                if existing.get("status") == "partial" and not RESUME_PARTIAL and not REPROCESS_EXISTING:
                    print(f"⏭️ 跳过部分完成笔记（已禁用续跑）: {note_id}")
                    continue

            print(f"🧩 处理第 {idx}/{len(items)} 条笔记: {note_id}")
            note_result = await process_one_note(client, item, existing)

            # 合并并立即写盘（保证任何中断时有最新进度）
            _merge_note_result_into_state(state, note_result)
            _save_processed_state(state)
            # 更新索引
            index[note_id] = note_result

            await asyncio.sleep(AI_INTERVAL_SEC)


    finally:
        await client.stop()
        print("✅ RPC客户端已停止")

    # 结束时再次保存一次确保 count 等聚合字段正确
    _save_processed_state(state)
    print(f"💾 已写入AI处理结果: {(PROJECT_ROOT / OUTPUT_AI_RESULT_PATH).as_posix()}")
    print(f"🧾 失败日志文件: {(PROJECT_ROOT / FAIL_LOG_PATH).as_posix()}")


if __name__ == "__main__":
    asyncio.run(main())