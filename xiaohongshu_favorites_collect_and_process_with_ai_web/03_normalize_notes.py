import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from utils.file_utils import read_json_with_project_root, write_json_with_project_root, PROJECT_ROOT

# 输入/输出文件路径（相对项目根目录）
INPUT_DETAILS_PATH = "data/favorite_notes_details.json"
OUTPUT_NORMALIZED_PATH = "data/favorite_notes_normalized.json"


def to_half_width(s: str) -> str:
    """全角转半角，并做 NFKC 规范化。"""
    if not s:
        return ""
    # 使用 unicode 规范化将宽字符折叠
    s = unicodedata.normalize("NFKC", s)
    return s


def strip_emojis(text: str) -> str:
    """尽量去掉 emoji 等符号字符，保留常见中英文、数字、标点。"""
    if not text:
        return ""
    # 先做兼容性规范化减少变体
    text = unicodedata.normalize("NFKC", text)
    # 过滤掉类别为 So（Symbol, other）和 Cs（Surrogate）的字符
    return "".join(ch for ch in text if unicodedata.category(ch) not in {"So", "Cs"})


def clean_text(text: Optional[str]) -> str:
    """清洗文本：去 emoji、压缩多余空白、去首尾空白。"""
    if not text:
        return ""
    text = strip_emojis(text)
    # 将各种空白折叠为一个空格
    text = re.sub(r"\s+", " ", text, flags=re.MULTILINE).strip()
    return text


def safe_int(val: Any, default: int = 0) -> int:
    try:
        if val is None:
            return default
        if isinstance(val, bool):
            return int(val)
        if isinstance(val, (int, float)):
            return int(val)
        s = str(val).strip().replace(",", "")
        # 提取前导数字（如 "123 个" -> 123）
        m = re.search(r"-?\d+", s)
        return int(m.group()) if m else default
    except Exception:
        return default


def normalize_tags(tags: Optional[List[str]]) -> List[str]:
    if not tags:
        return []
    normed: List[str] = []
    seen = set()
    for t in tags:
        if t is None:
            continue
        t = to_half_width(str(t)).strip().lower()
        # 去掉前缀话题格式如 #话题#、【】、[]等包裹符
        t = re.sub(r"^[#\s]+|[\s#]+$", "", t)
        t = t.strip("[]（）()【】<>")
        if not t:
            continue
        if t not in seen:
            seen.add(t)
            normed.append(t)
    return normed


def pick_video_duration_sec(video: Any) -> int:
    if not isinstance(video, dict):
        return 0
    # 常见字段名兜底
    for key in [
        "duration", "duration_sec", "durationSeconds", "length", "length_sec",
        "video_duration", "videoDuration", "time", "time_sec", "duration_ms"
    ]:
        if key in video and video[key] is not None:
            v = video[key]
            # 毫秒字段
            if key.endswith("_ms"):
                return safe_int(v) // 1000
            return safe_int(v)
    return 0


def to_iso8601_from_epoch_ms(epoch: Any) -> Optional[str]:
    try:
        # 兼容秒/毫秒
        ts = float(epoch)
        if ts > 1e12:  # 似乎是毫秒
            ts = ts / 1000.0
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")
    except Exception:
        return None


def parse_published_at(item: Dict[str, Any]) -> Optional[str]:
     # 优先使用抓取到的 date（可能为毫秒/秒时间戳，或 ISO 字符串）
     if "date" in item and item["date"] is not None:
         val = item["date"]
         # 先尝试按 epoch（字符串或数字）解析
         iso = to_iso8601_from_epoch_ms(val)
         if iso:
             return iso
         # 再尝试 ISO 文本解析
         if isinstance(val, str) and val:
             try:
                 dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                 if dt.tzinfo is None:
                     dt = dt.replace(tzinfo=timezone.utc)
                 return dt.isoformat().replace("+00:00", "Z")
             except Exception:
                 pass
     # 其次尝试直接解析 ISO 字符串（timestamp 字段）
     ts = item.get("timestamp")
     if isinstance(ts, str) and ts:
         try:
             dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
             if dt.tzinfo is None:
                 dt = dt.replace(tzinfo=timezone.utc)
             return dt.isoformat().replace("+00:00", "Z")
         except Exception:
             pass
     return None


def compute_age_days(published_at_iso: Optional[str]) -> Optional[int]:
    if not published_at_iso:
        return None
    try:
        dt = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        delta = now - dt
        # 取非负天数
        days = max(0, int(delta.total_seconds() // 86400))
        return days
    except Exception:
        return None


def detect_lang(title: str, desc: str) -> str:
    """启发式语言检测：中文字符比例 / 英文字母比例"""
    text = f"{title} {desc}".strip()
    if not text:
        return "unknown"
    # 统计中英字符
    zh_count = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    en_count = sum(1 for ch in text if ("a" <= ch <= "z") or ("A" <= ch <= "Z"))
    total = len(text)
    zh_ratio = zh_count / total
    en_ratio = en_count / total
    if zh_ratio >= 0.3:
        return "zh"
    if en_ratio >= 0.5:
        return "en"
    return "unknown"


def build_author_link(platform: str, user_id: str, user_xsec_token: str) -> Optional[str]:
    if not user_id:
        return None
    if platform == "xhs":
        return f"https://www.xiaohongshu.com/user/profile/{user_id}?xsec_token={user_xsec_token}"
    if platform == "bilibili":
        return f"https://space.bilibili.com/{user_id}"
    if platform == "zhihu":
        return f"https://www.zhihu.com/people/{user_id}"
    if platform == "weixin":
        # 公众号作者主页不固定，这里返回 None
        return None
    return None


def normalize_one(item: Dict[str, Any], platform: str = "xhs") -> Dict[str, Any]:
    note_id = str(item.get("id", "")).strip()
    note_xsec_token = item.get("xsec_token")
    raw_title = item.get("title") or ""
    raw_desc = item.get("desc") or ""
    title = clean_text(raw_title)
    # desc 原样保留，但计算长度时做简单 strip
    desc = raw_desc if isinstance(raw_desc, str) else str(raw_desc)
    desc_length = len(desc.strip())

    tags = item.get("tags") or []
    tags_norm = normalize_tags(tags)

    images = item.get("images") if isinstance(item.get("images"), list) else []
    video = item.get("video")
    has_images = bool(images)
    has_video = video is not None
    image_count = len(images) if has_images else 0
    video_duration_sec = pick_video_duration_sec(video)

    published_at = parse_published_at(item)
    age_days = compute_age_days(published_at)

    # 互动数据
    stat = item.get("statistic") or {}
    like_num = safe_int(stat.get("like_num", item.get("like_num")))
    collect_num = safe_int(stat.get("collect_num", item.get("collect_num")))
    # 评论数：优先 statistic.chat_num，其次根字段 comment_num
    comment_num = safe_int(stat.get("chat_num", item.get("comment_num")))
    engagement_score = like_num + collect_num + comment_num

    # 作者信息
    author_info = item.get("author_info") or {}
    user_id = str(author_info.get("user_id", "")).strip()
    user_xsec_token = author_info.get("xsec_token")
    username = clean_text(author_info.get("username"))
    avatar = author_info.get("avatar") or None
    author_link = build_author_link(platform, user_id, user_xsec_token)

    # 语言与质量标记
    lang = detect_lang(title, desc)
    # 是否存在视频字幕：若 video 为 dict 且存在非空 subtitles 字段，则认为有字幕
    has_video_subtitles = bool(video and isinstance(video, dict) and video.get("subtitles"))
    is_content_sparse = (desc_length < 50) and (not has_video_subtitles)
    has_only_media = (desc_length == 0) and (has_images or has_video)

    normalized = {
        "platform": platform,
        "note_id": note_id,
        "note_xsec_token": note_xsec_token,
        "title": title,
        "desc": desc,
        "desc_length": desc_length,
        "tags": tags_norm,
        "media": {
            "has_images": has_images,
            "has_video": has_video,
            "image_count": image_count,
            "video_duration_sec": video_duration_sec,
        },
        "timestamps": {
            "published_at": published_at,  # ISO8601 or None
            "age_days": age_days,
        },
        "stats": {
            "like_num": like_num,
            "collect_num": collect_num,
            "comment_num": comment_num,
            "engagement_score": engagement_score,
            "engagement_rate": None,  # 需要作者粉丝数后计算
        },
        "author": {
            "user_id": user_id,
            "username": username,
            "avatar": avatar,
            "author_link": author_link,
        },
        "locale": {
            "lang": lang,
        },
        "quality_flags": {
            "is_content_sparse": is_content_sparse,
            "has_only_media": has_only_media,
        },
    }
    return {"normalized": normalized}


def normalize_all() -> Dict[str, Any]:
    src = read_json_with_project_root(INPUT_DETAILS_PATH)
    # 兼容不同结构：可能是 {"data": [...]} 或 直接是列表
    items: List[Dict[str, Any]]
    if isinstance(src, dict):
        items = src.get("data") or []
    elif isinstance(src, list):
        items = src
    else:
        items = []

    normalized_list: List[Dict[str, Any]] = []
    for it in items:
        try:
            normalized_list.append(normalize_one(it, platform="xhs"))
        except Exception as e:
            # 忽略单条异常，保证整体可用
            normalized_list.append({
                "error": str(e),
                "raw_id": it.get("id") if isinstance(it, dict) else None,
            })

    result = {
        "platform": "xhs",
        "count": len([d for d in normalized_list if "normalized" in d]),
        "data": normalized_list,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_file": INPUT_DETAILS_PATH,
    }
    return result


def main():
    result = normalize_all()
    write_json_with_project_root(OUTPUT_NORMALIZED_PATH, result)
    print(f"✅ 规范化完成，输出文件：{(PROJECT_ROOT / OUTPUT_NORMALIZED_PATH).as_posix()}，count={result.get('count')}")


if __name__ == "__main__":
    print("🚀 开始规范化收藏笔记数据 …")
    main()