"""LLM API Key 的本地持久化（明文，仅限个人机器使用）。"""

import json
import os

from .config import DATA_DIR

SECRETS_FILE = DATA_DIR / "secrets.json"


def load_api_key() -> str:
    try:
        data = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    return data.get("api_key", "") if isinstance(data, dict) else ""


def save_api_key(api_key: str) -> None:
    tmp = SECRETS_FILE.parent / (SECRETS_FILE.name + ".tmp")
    try:
        tmp.write_text(
            json.dumps({"api_key": api_key}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, SECRETS_FILE)
    except OSError:
        pass


def clear_api_key() -> None:
    try:
        os.remove(SECRETS_FILE)
    except OSError:
        pass
