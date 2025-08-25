import json
import os
from pathlib import Path
from typing import Any


def get_root_dir():
    try:
        # 如果在脚本中运行，有 __file__
        return Path(__file__).resolve().parent.parent
    except NameError:
        # 如果在交互环境（如 Jupyter 或 REPL），__file__ 不存在
        return Path(os.getcwd()).resolve().parent

PROJECT_ROOT = get_root_dir()


def read_json_with_project_root(file_path: str) -> Any:
    """读取项目根目录下的JSON文件

    Args:
        file_path: 相对于项目根目录的文件路径

    Returns:
        解析后的JSON数据
    """
    with open(os.path.join(PROJECT_ROOT, file_path), 'r', encoding='utf-8') as f:
        return json.loads(f.read())


def write_json_with_project_root(file_path: str, data: Any) -> None:
    """写入JSON数据到项目根目录下的文件

    Args:
        data: 要写入的数据
        file_path: 相对于项目根目录的文件路径
    """
    with open(os.path.join(PROJECT_ROOT, file_path), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

