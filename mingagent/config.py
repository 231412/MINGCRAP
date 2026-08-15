import os
import sys
from pathlib import Path


APP_NAME = "MINGAGENT"

# 代码根目录（开发模式下同时是数据目录）
ROOT_DIR = Path(__file__).resolve().parent.parent

# 是否为 PyInstaller 冻结运行
FROZEN = bool(getattr(sys, "frozen", False))


def _data_dir() -> Path:
    """数据目录解析顺序：环境变量 > 冻结时 %APPDATA%\\MINGAGENT > 项目根目录。

    冻结运行时代码目录是只读的临时解包目录，所有可写数据必须落在这里。
    """
    env_dir = os.environ.get("MINGAGENT_DATA_DIR")
    if env_dir:
        base = Path(env_dir)
    elif FROZEN:
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    else:
        base = ROOT_DIR
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return base


# 数据目录：设置 / 密钥 / 经验 / 历史 / 审计 / 会话快照
DATA_DIR = _data_dir()

# 工具执行的工作目录：冻结时用 exe 所在目录（用户可自选工作位置），否则项目根目录
WORK_DIR = Path(sys.executable).resolve().parent if FROZEN else ROOT_DIR

EXPERTISE_FILE = DATA_DIR / "expertise.json"
HISTORY_FILE = DATA_DIR / "history.json"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
SESSIONS_DIR = DATA_DIR / "sessions"

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
MODEL_OPTIONS = [
    "deepseek-chat",
    "deepseek-reasoner",
    "gpt-4o-mini",
    "gpt-4.1",
    "自定义",
]

DEFAULT_STEP_LIMIT = 10
MAX_STEP_LIMIT = 20
MAX_CONTEXT_MESSAGES = 24
MAX_OBSERVATION_CHARS = 6000
MAX_TOOL_OUTPUT_CHARS = 12000

ENV_TOOLS = [
    ("python", "python --version"),
    ("node", "node -v"),
    ("git", "git --version"),
    ("npm", "npm -v"),
]

DANGER_PATTERNS = [
    r"\brmdir\b",
    r"\bdel\b",
    r"\berase\b",
    r"\bformat\b",
    r"\bdiskpart\b",
    r"\bshutdown\b",
    r"\bstop-computer\b",
    r"\brestart-computer\b",
    r"\bremove-item\b",
    r"\bclear-disk\b",
    r"\breg\s+(add|delete)\b",
    r"\bnet\s+user\b",
    r"\btaskkill\b",
    r"\bbcdedit\b",
    r"\bsc\s+delete\b",
    r"\bicacls\b",
    r"\bcipher\s+/w\b",
    r"\bwevtutil\s+cl\b",
    r"powershell[^\r\n]*\s-enc(?:odedcommand)?\b",
    r"curl[^\r\n]*iex\b",
]
