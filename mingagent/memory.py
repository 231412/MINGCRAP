import json
import os
import re
import time

from .config import EXPERTISE_FILE

_PATH_RE = re.compile(r'"[A-Za-z]:\\[^"]*"|[A-Za-z]:\\[^\s"]+')


def sanitize_command(command: str) -> str:
    """归一化命令：压缩空白并脱敏绝对路径，用于经验库存储。"""
    command = " ".join((command or "").split())
    command = _PATH_RE.sub("<path>", command)
    return command.strip()


def load_expertise() -> list[dict]:
    if not EXPERTISE_FILE.exists():
        return []
    try:
        data = json.loads(EXPERTISE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _atomic_write(path, text: str) -> None:
    """先写临时文件再替换，避免并发读写时读到半截 JSON。"""
    tmp = path.parent / (path.name + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass


def commit_expertise(task: str, commands: list[str]) -> None:
    """任务成功后一次性提交经验：脱敏、归一化去重、按时间倒序、上限 20 条。"""
    if not commands:
        return

    data = load_expertise()
    keys = {
        sanitize_command(item.get("cmd", "")).lower()
        for item in data
        if item.get("cmd")
    }
    now = time.time()
    for command in commands:
        clean = sanitize_command(command)
        if len(clean) < 3:
            continue
        key = clean.lower()
        if key in keys:
            continue
        keys.add(key)
        data.append({"task": task[:80], "cmd": clean, "ts": now})

    data.sort(key=lambda item: item.get("ts", 0), reverse=True)
    data = data[:20]
    _atomic_write(
        EXPERTISE_FILE,
        json.dumps(data, ensure_ascii=False, indent=2),
    )


def delete_expertise(command: str) -> None:
    data = load_expertise()
    data = [item for item in data if item.get("cmd") != command]
    _atomic_write(
        EXPERTISE_FILE,
        json.dumps(data, ensure_ascii=False, indent=2),
    )
