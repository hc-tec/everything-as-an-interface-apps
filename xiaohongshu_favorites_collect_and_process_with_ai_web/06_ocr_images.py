import os
import json
import asyncio
from typing import Dict, Any

from client_sdk.params import TaskParams
from client_sdk.rpc_client import EAIRPCClient  # type: ignore
from utils.file_utils import PROJECT_ROOT

# ----------------------
# Config
# ----------------------
IMAGES_DIR = PROJECT_ROOT / "data" / "images"
OUTPUT_PATH = PROJECT_ROOT / "data" / "ocr_results.json"

# RPC client config（与现有脚本保持一致）
RPC_BASE_URL = "http://127.0.0.1:8008"
RPC_API_KEY = "testkey"
RPC_WEBHOOK_HOST = "127.0.0.1"
RPC_WEBHOOK_PORT = 0

# ----------------------
# IO helpers
# ----------------------

def _load_results() -> Dict[str, Any]:
    if not os.path.exists(OUTPUT_PATH):
        return {}
    try:
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_results(data: Dict[str, Any]) -> None:
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ----------------------
# Main logic
# ----------------------

async def process_one_image(client: EAIRPCClient, abs_path: str) -> Dict[str, Any]:
    # 直接按你的示例调用 OCR（cookie_ids 为空）
    res = await client.call_paddle_ocr(
        image_path_abs_path=abs_path,
        task_params=TaskParams(
            cookie_ids=[],
            close_page_when_task_finished=True,
        ),
    )
    return res


async def main():
    # 读取已存在的结果，避免重复处理
    results: Dict[str, Any] = _load_results()

    # 初始化 RPC 客户端
    client = EAIRPCClient(
        base_url=RPC_BASE_URL,
        api_key=RPC_API_KEY,
        webhook_host=RPC_WEBHOOK_HOST,
        webhook_port=RPC_WEBHOOK_PORT,
    )

    await client.start()
    print("✅ RPC客户端已启动")

    try:
        # 遍历 data/images 下的所有图片文件
        if not os.path.exists(IMAGES_DIR):
            print(f"[warn] 图片目录不存在: {IMAGES_DIR}")
            return

        total = 0
        skipped = 0
        ok_cnt = 0
        fail_cnt = 0

        for note_id in os.listdir(IMAGES_DIR):
            note_dir = IMAGES_DIR / note_id
            if not os.path.isdir(note_dir):
                continue

            for fname in os.listdir(note_dir):
                fpath = note_dir / fname
                if not os.path.isfile(fpath):
                    continue

                image_id = fname  # 以图片文件名作为唯一ID
                total += 1

                # 跳过已有结果
                if image_id in results:
                    skipped += 1
                    continue

                abs_path = str(fpath.resolve())
                try:
                    ocr_res = await process_one_image(client, abs_path)
                    # 将完整返回结构保存，便于后续调试/复用
                    results[image_id] = ocr_res
                    ok_cnt += 1
                    print(f"[OK] {note_id}/{fname}")
                except Exception as e:
                    results[image_id] = {
                        "success": False,
                        "error": str(e),
                        "image_path": abs_path,
                    }
                    fail_cnt += 1
                    print(f"[FAIL] {note_id}/{fname} -> {e}")
                finally:
                    # 每处理一张图片就落盘，保证中断可续跑
                    _save_results(results)
                    # 略作延迟，避免触发风控
                    await asyncio.sleep(0.05)

        print(f"[done] 总数 {total}, 成功 {ok_cnt}, 失败 {fail_cnt}, 跳过 {skipped}")
    finally:
        try:
            await client.stop()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())