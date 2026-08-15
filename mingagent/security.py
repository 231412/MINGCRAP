"""统一的安全评估：命令 / Python 风险拦截、安全模式白名单与审计日志。

设计原则：
- `assess_risk` 是所有工具动作执行前的唯一入口，cmd 与 python 共用；
- Python 载荷用 AST 静态扫描 + 正则兜底识别危险调用与写操作；
- cmd 载荷用扩展黑名单 + 链式执行 / 重定向检测识别危险命令；
- 安全模式下 cmd 仅允许只读白名单自动执行，其余一律人工确认；
- 所有风险判定与执行结果追加写入 `audit.jsonl`。
"""

import ast
import json
import re
import time
from typing import Any

from .config import AUDIT_FILE, DANGER_PATTERNS

# ---------------------------------------------------------------------------
# cmd 危险检测
# ---------------------------------------------------------------------------

# 在原黑名单（config.DANGER_PATTERNS）基础上补充别名与组合变体
CMD_EXTRA_DANGER_PATTERNS = [
    r"\brd\b",                       # rmdir 的别名
    r"rmdir\s+/s",                   # 递归删除目录树
    r"del\s+.*/(s|q)",               # del 递归 / 静默
    r"remove-item[^\r\n]*-recurse",
    r"format\s+[a-z]:",              # format 指定盘符
    r"\bclean\s+all\b",              # diskpart clean all
    r"\bset-acl\b",                  # 修改权限
    r"\btakeown\b",
    r"\bcacls\b",
    r"\battrib\s+.*[-+][sh]\b",      # 修改系统 / 隐藏属性
    r"\bwmic\s+.*\bdelete\b",        # WMI 删除
]

CMD_DANGER_RULES = DANGER_PATTERNS + CMD_EXTRA_DANGER_PATTERNS

# 链式执行 / 重定向运算符
CHAIN_OPERATORS = ("&&", "||", "&", "|", ";", ">", ">>", "<", "^")

# 安全模式：出现这些运算符一律不自动放行（| 允许，仅用于只读管道）
SAFE_MODE_BLOCK_OPS = ("&&", "&", ";", ">", ">>", "<", "^")


def detect_dangerous_cmd(command: str) -> str | None:
    """返回危险原因；安全时返回 None。"""
    text = (command or "").strip()
    if not text:
        return None

    for pattern in CMD_DANGER_RULES:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            snippet = match.group(0).strip()[:40]
            return f"命中危险规则（{snippet}）"

    # 链式执行 / 重定向可能夹带危险操作
    if any(op in text for op in CHAIN_OPERATORS):
        for segment in re.split(r"&&|\|\||[&|;<>^]", text):
            for pattern in CMD_DANGER_RULES:
                if re.search(pattern, segment, re.IGNORECASE):
                    snippet = segment.strip()[:40]
                    return f"链式执行/重定向夹带危险操作（{snippet}）"
    return None


# ---------------------------------------------------------------------------
# 安全模式只读白名单
# ---------------------------------------------------------------------------

SAFE_CMD_PATTERNS = [
    r"^cd\b", r"^chdir\b", r"^dir\b", r"^where\b", r"^echo\b",
    r"^type\b", r"^more\b", r"^findstr\b", r"^tasklist\b", r"^netstat\b",
    r"^ipconfig\b", r"^systeminfo\b", r"^whoami\b", r"^ver\b", r"^set\b",
    r"^path\b", r"^hostname\b", r"^assoc\b", r"^ftype\b",
    r"^python\b[^\r\n]*(--version|-v)\b",
    r"^node\s+(-v|--version)\b",
    r"^npm\s+(list|ls|view|--version)\b",
    r"^pip\s+(list|show|freeze|--version)\b",
    r"^git\s+(status|log|diff|show|branch|tag|remote\s+-v|config\s+--list|--version)\b",
    r"^powershell[^\r\n]*-command\s+\"?get-",
    r"^get-childitem\b", r"^get-content\b", r"^get-process\b",
    r"^get-service\b", r"^get-item\b", r"^get-location\b", r"^get-date\b",
    r"^get-command\b", r"^get-volume\b", r"^get-disk\b", r"^get-partition\b",
    r"^get-ciminstance\b", r"^get-acl\b", r"^get-history\b",
    r"^get-psdrive\b", r"^get-variable\b",
    r"^test-path\b", r"^measure-object\b", r"^select-object\b",
    r"^where-object\b", r"^sort-object\b", r"^format-table\b",
    r"^format-list\b", r"^out-string\b", r"^select-string\b",
    r"^compare-object\b", r"^group-object\b",
    r"^wmic\s+\S+\s+get\b",
]


def _normalize_cmd(command: str) -> str:
    text = (command or "").strip()
    text = re.sub(r"^cmd(?:\.exe)?\s+/c\s+", "", text, flags=re.IGNORECASE)
    text = text.strip().strip('"').strip("'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def matches_safe_cmd(command: str) -> bool:
    """安全模式：命令是否属于只读白名单。"""
    text = _normalize_cmd(command)
    if not text:
        return False
    if any(op in text for op in SAFE_MODE_BLOCK_OPS):
        return False
    lower = text.lower()
    return any(re.match(pattern, lower) for pattern in SAFE_CMD_PATTERNS)


# ---------------------------------------------------------------------------
# Python 代码静态扫描
# ---------------------------------------------------------------------------

BARE_DANGEROUS_IMPORTS = {"subprocess", "ctypes", "winreg", "socket", "importlib"}

SENSITIVE_MODULES = {"os", "shutil", "subprocess", "winreg", "ctypes", "socket", "importlib", "pathlib"}

PY_DANGEROUS_CALLS = {
    # 删除 / 系统级操作
    "os.remove", "os.unlink", "os.rmdir", "os.removedirs",
    "os.system", "os.popen", "os.startfile", "os.kill", "os.chmod", "os.chown",
    "os.spawnl", "os.spawnle", "os.spawnlp", "os.spawnlpe",
    "os.spawnv", "os.spawnve", "os.spawnvp", "os.spawnvpe",
    "os.execv", "os.execve", "os.execl", "os.execle", "os.execlp", "os.execlpe",
    "os.execvp", "os.execvpe",
    "shutil.rmtree",
    # 进程逃逸
    "subprocess.run", "subprocess.call", "subprocess.Popen",
    "subprocess.check_output", "subprocess.check_call",
    "subprocess.getoutput", "subprocess.getstatusoutput",
    # 注册表写入
    "winreg.CreateKey", "winreg.CreateKeyEx", "winreg.DeleteKey",
    "winreg.DeleteKeyEx", "winreg.DeleteValue", "winreg.SetValue",
    "winreg.SetValueEx", "winreg.SaveKey",
    # 原生代码 / 网络
    "ctypes.CDLL", "ctypes.WinDLL", "ctypes.OleDLL", "ctypes.pythonapi", "ctypes.cast",
    "socket.socket",
    # 动态执行
    "importlib.import_module",
    "eval", "exec", "compile", "__import__",
}

PY_MUTATING_CALLS = {
    "os.mkdir", "os.makedirs", "os.rename", "os.renames", "os.replace",
    "os.link", "os.symlink", "os.truncate",
    "shutil.copy", "shutil.copy2", "shutil.copyfile", "shutil.copytree",
    "shutil.move", "shutil.make_archive", "shutil.unpack_archive",
    "pathlib.Path.mkdir",
}

# 以裸方法名出现的文件写操作（如 Path("x").unlink()），按保守策略标记
BARE_MUTATING_ATTRS = {"unlink", "rmdir", "write_text", "write_bytes", "touch", "rename", "replace"}

# 正则兜底：捕捉 AST 定位不到的变体（含简单混淆），(标签, 模式)
RAW_DANGEROUS_RULES = [
    ("os/shutil 文件删除或系统调用", r"\b(?:os\.(?:remove|unlink|rmdir|removedirs|system|popen|startfile|kill)|shutil\.rmtree|socket\.socket)\s*\("),
    ("subprocess/winreg/ctypes 高风险模块", r"\b(subprocess|winreg|ctypes)\b"),
    ("eval/exec/__import__ 动态执行", r"\b(eval|exec|__import__)\s*\("),
    ("getattr 动态属性访问", r"getattr\s*\(\s*(?:os|shutil|subprocess|winreg|ctypes|socket|importlib)\b"),
]

RAW_MUTATING_RULES = [
    ("文件写/复制操作", r"\b(?:os\.(?:mkdir|makedirs|rename|renames|replace)|shutil\.(?:copy|copy2|copyfile|copytree|move))\s*\("),
    ("路径对象写操作", r"\.(unlink|rmdir|write_text|write_bytes|touch|rename|replace)\s*\("),
    ("open 写模式", r"\bopen\s*\([^)]*['\"](?:[wax]\+?|r\+)"),
]


def _dotted_name(node: ast.expr) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def _open_mode(node: ast.Call) -> str:
    if len(node.args) >= 2:
        arg = node.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
        return "w"  # 无法静态确定时按写模式处理
    for kw in node.keywords:
        if kw.arg == "mode":
            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                return kw.value.value
            return "w"
    return "r"


def analyze_python(code: str) -> tuple[list[str], list[str]]:
    """AST 静态扫描 Python 代码。

    返回 (危险调用列表, 写操作列表)。危险调用在两种模式下都需确认；
    写操作仅在安全模式下需确认。
    """
    danger: list[str] = []
    mutation: list[str] = []

    def add(target: list[str], name: str) -> None:
        if name not in target:
            target.append(name)

    try:
        tree = ast.parse(code)
    except SyntaxError:
        tree = None  # 无法解析的代码执行时会失败，本身无害

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = (alias.name or "").split(".")[0]
                    if root in BARE_DANGEROUS_IMPORTS:
                        add(danger, f"import {root}")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root in BARE_DANGEROUS_IMPORTS:
                    add(danger, f"from {root} import ...")
                elif root in {"os", "shutil"}:
                    for alias in node.names:
                        if alias.name in {"remove", "unlink", "rmdir", "system", "popen", "rmtree", "move"}:
                            add(danger, f"from {root} import {alias.name}")
            elif isinstance(node, ast.Call):
                name = _dotted_name(node.func)
                if name in PY_DANGEROUS_CALLS:
                    add(danger, name)
                elif name in PY_MUTATING_CALLS:
                    add(mutation, name)
                elif name in BARE_MUTATING_ATTRS:
                    add(mutation, f".{name}()")
                if name == "open":
                    mode = _open_mode(node)
                    if any(ch in mode for ch in ("w", "a", "x", "+")):
                        add(mutation, f"open(..., {mode!r})")
                if name == "getattr":
                    if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in SENSITIVE_MODULES:
                        add(danger, f"getattr({node.args[0].id}, ...)")

    # 正则兜底
    for label, pattern in RAW_DANGEROUS_RULES:
        if re.search(pattern, code, re.IGNORECASE):
            add(danger, label)
    for label, pattern in RAW_MUTATING_RULES:
        if re.search(pattern, code, re.IGNORECASE):
            add(mutation, label)

    return danger, mutation


# ---------------------------------------------------------------------------
# 统一入口与审计
# ---------------------------------------------------------------------------

def assess_risk(action: str, payload: str, safe_mode: bool) -> tuple[str, str]:
    """统一风险评估入口。

    返回 (verdict, reason)，verdict ∈ {"safe", "confirm"}。
    """
    if action == "search":
        return "safe", ""

    if action == "python":
        danger, mutation = analyze_python(payload)
        if danger:
            return "confirm", "Python 代码包含危险调用：" + "、".join(danger[:5])
        if safe_mode and mutation:
            return "confirm", "安全模式：Python 代码包含写操作：" + "、".join(mutation[:5])
        return "safe", ""

    if action == "cmd":
        reason = detect_dangerous_cmd(payload)
        if reason:
            return "confirm", reason
        if safe_mode and not matches_safe_cmd(payload):
            return "confirm", "安全模式：该命令不在只读白名单内，需人工确认"
        return "safe", ""

    return "safe", ""


def is_risky_command(command: str) -> bool:
    """兼容旧接口：仅检查 cmd 载荷是否命中危险规则。"""
    return detect_dangerous_cmd(command) is not None


def audit_log(entry: dict[str, Any]) -> None:
    """追加一条审计记录到 audit.jsonl。"""
    record = {"ts": time.time(), **entry}
    try:
        with AUDIT_FILE.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass


def read_recent_audit(limit: int = 5) -> list[dict]:
    """读取最近 limit 条审计记录（新的在前）。"""
    if not AUDIT_FILE.exists():
        return []
    try:
        lines = AUDIT_FILE.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[dict] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
        if len(records) >= limit:
            break
    return records
