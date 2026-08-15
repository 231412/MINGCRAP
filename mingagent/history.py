import json
import os
import time

from .config import HISTORY_FILE, SESSIONS_DIR


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
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


def save_history_entry(
    title: str,
    status: str,
    summary: str = "",
    events: list | None = None,
    messages: list | None = None,
) -> None:
    entry = {
        "id": f"{int(time.time() * 1000)}",
        "title": (title or "Untitled")[:80],
        "status": status,
        "summary": (summary or "")[:300],
        "ts": time.time(),
    }
    if events is not None or messages is not None:
        entry["snapshot"] = True
        try:
            SESSIONS_DIR.mkdir(exist_ok=True)
        except OSError:
            pass
        _atomic_write(
            SESSIONS_DIR / f"{entry['id']}.json",
            json.dumps(
                {"events": events or [], "messages": messages or []},
                ensure_ascii=False,
            ),
        )

    data = load_history()
    data.insert(0, entry)
    data = data[:30]
    _atomic_write(
        HISTORY_FILE,
        json.dumps(data, ensure_ascii=False, indent=2),
    )


def load_snapshot(entry_id: str) -> dict | None:
    """读取某条历史记录的会话快照（events + messages）。"""
    path = SESSIONS_DIR / f"{entry_id}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    return {
        "events": data.get("events") or [],
        "messages": data.get("messages") or [],
    }
