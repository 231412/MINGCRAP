"""界面偏好设置：主题与强调色，持久化到 settings.json。"""

import json
import os

from .config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "settings.json"

THEME_OPTIONS = {
    "暗色": "dark",
    "亮色": "light",
}

ACCENT_OPTIONS = {
    "终端白": "#F5F5F5",
    "青色": "#2DD4BF",
    "紫色": "#A78BFA",
    "绿色": "#4ADE80",
    "橙色": "#FB923C",
    "蓝色": "#60A5FA",
}

DEFAULTS = {"theme": "dark", "accent": "#F5F5F5"}


def load_settings() -> dict:
    settings = dict(DEFAULTS)
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return settings
    if isinstance(data, dict):
        if data.get("theme") in THEME_OPTIONS.values():
            settings["theme"] = data["theme"]
        if data.get("accent") in ACCENT_OPTIONS.values():
            settings["accent"] = data["accent"]
    return settings


def save_settings(theme: str, accent: str) -> None:
    tmp = SETTINGS_FILE.parent / (SETTINGS_FILE.name + ".tmp")
    try:
        tmp.write_text(
            json.dumps({"theme": theme, "accent": accent}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, SETTINGS_FILE)
    except OSError:
        pass
