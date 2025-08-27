import os
import sys
import json
import time
import errno
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from utils.file_utils import read_json_with_project_root, PROJECT_ROOT

# ----------------------
# Config
# ----------------------
INPUT_DETAILS_PATH = "data/favorite_notes_details.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "images"
DEFAULT_REFERER = "https://www.xiaohongshu.com/"

# User-Agent 模拟常见浏览器，避免被CDN/防火墙拦截
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
)

# ----------------------
# Helpers
# ----------------------

def ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def sanitize_filename(name: str) -> str:
    # Windows 非法字符过滤: \\ / : * ? " < > |
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, '_')
    # 去除控制字符
    name = ''.join(c if 32 <= ord(c) < 127 else '_' for c in name)
    # 避免过长
    return name[:200] if len(name) > 200 else name


def pick_filename_from_url(url: str, fallback: str) -> str:
    path = urlsplit(url).path
    base = os.path.basename(path) or fallback
    base = sanitize_filename(base)
    if not os.path.splitext(base)[1]:
        # 没有扩展名时，尝试根据URL中可能的格式提示，默认 .jpg
        if 'webp' in url.lower():
            base += '.webp'
        elif 'png' in url.lower():
            base += '.png'
        else:
            base += '.jpg'
    return base


def load_cookies_from_env_or_file(arg_path: Optional[str]) -> Optional[List[Dict[str, Any]]]:
    # 1) 命令行参数文件
    if arg_path:
        try:
            with open(arg_path, 'r', encoding='utf-8') as f:
                obj = json.load(f)
            if isinstance(obj, dict) and 'cookies' in obj and isinstance(obj['cookies'], list):
                return obj['cookies']
            if isinstance(obj, list):
                return obj
        except Exception as e:
            print(f"[warn] 加载 cookies 文件失败：{e}")
    # 2) 环境变量 XHS_COOKIES_JSON
    env_val = os.getenv('XHS_COOKIES_JSON')
    if env_val:
        try:
            obj = json.loads(env_val)
            if isinstance(obj, dict) and 'cookies' in obj and isinstance(obj['cookies'], list):
                return obj['cookies']
            if isinstance(obj, list):
                return obj
        except Exception as e:
            print(f"[warn] 解析环境变量 XHS_COOKIES_JSON 失败：{e}")
    # 3) 默认路径 data/xhs_cookies.json（如果存在）
    default_cookie_path = PROJECT_ROOT / 'data' / 'xhs_cookies.json'
    if os.path.exists(default_cookie_path):
        try:
            with open(default_cookie_path, 'r', encoding='utf-8') as f:
                obj = json.load(f)
            if isinstance(obj, dict) and 'cookies' in obj and isinstance(obj['cookies'], list):
                return obj['cookies']
            if isinstance(obj, list):
                return obj
        except Exception as e:
            print(f"[warn] 解析 {default_cookie_path} 失败：{e}")
    return None


def build_cookie_header(cookies: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not cookies:
        return None
    # 直接拼接为 name=value; 的形式（仅用于简单直连CDN，不做域过滤）
    parts: List[str] = []
    for c in cookies:
        name = c.get('name')
        value = c.get('value')
        if isinstance(name, str) and isinstance(value, (str, int, float)):
            parts.append(f"{name}={value}")
    return '; '.join(parts) if parts else None


def make_headers(cookie_header: Optional[str]) -> Dict[str, str]:
    headers = {
        'User-Agent': UA,
        'Referer': DEFAULT_REFERER,
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    if cookie_header:
        headers['Cookie'] = cookie_header
    return headers


def download_one(url: str, dst_path: str, headers: Dict[str, str], retries: int = 3, timeout: int = 20) -> Tuple[bool, Optional[str]]:
    # 跳过已存在且非空
    if os.path.exists(dst_path) and os.path.getsize(dst_path) > 0:
        return True, None

    last_err: Optional[str] = None
    for attempt in range(1, retries + 1):
        try:
            req = Request(url=url, headers=headers, method='GET')
            with urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    last_err = f"HTTP {resp.status}"
                else:
                    data = resp.read()
                    ensure_dir(os.path.dirname(dst_path))
                    with open(dst_path, 'wb') as f:
                        f.write(data)
                    return True, None
        except HTTPError as e:
            last_err = f"HTTPError {e.code}: {e.reason}"
        except URLError as e:
            last_err = f"URLError: {e.reason}"
        except Exception as e:
            last_err = f"Exception: {e}"
        # 退避等待
        sleep_sec = min(1.0 * attempt, 5.0)
        time.sleep(sleep_sec)
    return False, last_err


# ----------------------
# Main
# ----------------------

def run(cookies_path: Optional[str] = None) -> None:
    # 读取笔记详情数据
    details: Dict[str, Any] = read_json_with_project_root(INPUT_DETAILS_PATH)
    notes: List[Dict[str, Any]] = details.get('data', []) if isinstance(details, dict) else []

    if not notes:
        print("[info] 未在 data/favorite_notes_details.json 中发现可用数据")
        return

    # 读取 cookies（可选）并组装请求头
    cookies_list = load_cookies_from_env_or_file(cookies_path)
    cookie_header = build_cookie_header(cookies_list)
    headers = make_headers(cookie_header)

    total = 0
    ok_cnt = 0
    fail_cnt = 0

    print(f"[info] 将下载到: {OUTPUT_DIR}")

    for note in notes:
        note_id = note.get('id') or 'unknown'
        images: List[str] = note.get('images', []) or []
        if not images:
            continue

        save_dir = os.path.join(str(OUTPUT_DIR), sanitize_filename(str(note_id)))
        ensure_dir(save_dir)

        for idx, url in enumerate(images, start=1):
            total += 1
            base_name = pick_filename_from_url(url, f"{idx}.jpg")
            dst = os.path.join(save_dir, base_name)
            ok, err = download_one(url, dst, headers)
            if ok:
                ok_cnt += 1
                print(f"[OK] {note_id} -> {base_name}")
            else:
                fail_cnt += 1
                print(f"[FAIL] {note_id} -> {base_name} | {url} | {err}")
            # 轻微限速，避免触发风控
            time.sleep(2)

    print(f"[done] 完成: 成功 {ok_cnt} / 失败 {fail_cnt} / 总数 {total}")


if __name__ == '__main__':
    # 可选参数：python 05_download_images.py [cookies_json_path]
    arg_path = sys.argv[1] if len(sys.argv) > 1 else None
    run(cookies_path=arg_path)