import locale
import os
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass

import requests

from .config import MAX_OBSERVATION_CHARS, MAX_TOOL_OUTPUT_CHARS, WORK_DIR
from .security import is_risky_command  # 兼容导出

CMD_TIMEOUT_SECONDS = 30
PY_TIMEOUT_SECONDS = 20


@dataclass
class ToolResult:
    action: str
    payload: str
    ok: bool
    stdout: str
    stderr: str
    elapsed: float
    truncated: bool = False
    cancelled: bool = False

    @property
    def output(self) -> str:
        if self.stderr:
            return f"{self.stdout}\n{self.stderr}".strip()
        return self.stdout.strip()


def _limit_output(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_TOOL_OUTPUT_CHARS:
        return text, False
    return text[:MAX_TOOL_OUTPUT_CHARS] + "\n...[输出已截断]", True


def _result(
    action: str,
    payload: str,
    returncode: int,
    stdout: str,
    stderr: str,
    elapsed: float,
) -> ToolResult:
    combined = stdout if stdout else ""
    if stderr:
        combined = f"{combined}\n{stderr}".strip()
    combined, truncated = _limit_output(combined)
    return ToolResult(
        action=action,
        payload=payload,
        ok=returncode == 0,
        stdout=combined,
        stderr="",
        elapsed=elapsed,
        truncated=truncated,
    )


def _decode_bytes(data: bytes) -> str:
    """子进程输出解码：utf-8 → gbk → 系统默认，最后兜底替换。"""
    candidates = ["utf-8", "gbk"]
    preferred = locale.getpreferredencoding(False)
    if preferred and preferred.lower() not in ("utf-8", "gbk"):
        candidates.append(preferred)
    for encoding in candidates:
        try:
            return data.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def _kill_tree(proc: subprocess.Popen) -> None:
    """结束整个进程树（Windows 下通过 taskkill /T）。"""
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _wait_process(
    proc: subprocess.Popen,
    cancel_event,
    timeout_sec: float,
) -> tuple:
    """轮询等待子进程，支持取消与超时；输出由后台线程持续排空以防管道阻塞。

    返回 (returncode, stdout_bytes, stderr_bytes, cancelled, timed_out)。
    """
    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []

    def _drain(pipe, target) -> None:
        try:
            target.append(pipe.read() or b"")
        except Exception:
            pass

    readers = [
        threading.Thread(target=_drain, args=(proc.stdout, stdout_chunks), daemon=True),
        threading.Thread(target=_drain, args=(proc.stderr, stderr_chunks), daemon=True),
    ]
    for thread in readers:
        thread.start()

    started = time.perf_counter()
    cancelled = False
    timed_out = False
    while proc.poll() is None:
        if cancel_event is not None and cancel_event.is_set():
            cancelled = True
            _kill_tree(proc)
            break
        if time.perf_counter() - started > timeout_sec:
            timed_out = True
            _kill_tree(proc)
            break
        time.sleep(0.1)

    for thread in readers:
        thread.join(timeout=1.0)

    return proc.poll(), b"".join(stdout_chunks), b"".join(stderr_chunks), cancelled, timed_out


def execute_cmd(command: str, cancel_event=None) -> ToolResult:
    started = time.perf_counter()
    try:
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(WORK_DIR),
            **kwargs,
        )
    except Exception as exc:
        return ToolResult(
            action="cmd",
            payload=command,
            ok=False,
            stdout="",
            stderr=str(exc),
            elapsed=time.perf_counter() - started,
        )

    returncode, out_bytes, err_bytes, cancelled, timed_out = _wait_process(
        proc, cancel_event, CMD_TIMEOUT_SECONDS
    )
    elapsed = time.perf_counter() - started

    if cancelled:
        return ToolResult(
            action="cmd",
            payload=command,
            ok=False,
            stdout="",
            stderr="命令已由用户停止",
            elapsed=elapsed,
            cancelled=True,
        )
    if timed_out:
        return ToolResult(
            action="cmd",
            payload=command,
            ok=False,
            stdout="",
            stderr=f"命令执行超时（{CMD_TIMEOUT_SECONDS}s）",
            elapsed=elapsed,
        )

    return _result(
        "cmd",
        command,
        returncode if returncode is not None else -1,
        _decode_bytes(out_bytes),
        _decode_bytes(err_bytes),
        elapsed,
    )


def execute_python(code: str, cancel_event=None) -> ToolResult:
    started = time.perf_counter()
    tmp_path = ""
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="mingagent_", text=True)
        os.close(fd)
        with open(tmp_path, "w", encoding="utf-8") as file:
            file.write(code)

        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        proc = subprocess.Popen(
            [sys.executable, tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(WORK_DIR),
            **kwargs,
        )
    except Exception as exc:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return ToolResult(
            action="python",
            payload=code,
            ok=False,
            stdout="",
            stderr=str(exc),
            elapsed=time.perf_counter() - started,
        )

    returncode, out_bytes, err_bytes, cancelled, timed_out = _wait_process(
        proc, cancel_event, PY_TIMEOUT_SECONDS
    )
    elapsed = time.perf_counter() - started

    if tmp_path:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    if cancelled:
        return ToolResult(
            action="python",
            payload=code,
            ok=False,
            stdout="",
            stderr="Python 已由用户停止",
            elapsed=elapsed,
            cancelled=True,
        )
    if timed_out:
        return ToolResult(
            action="python",
            payload=code,
            ok=False,
            stdout="",
            stderr=f"Python 执行超时（{PY_TIMEOUT_SECONDS}s）",
            elapsed=elapsed,
        )

    return _result(
        "python",
        code,
        returncode if returncode is not None else -1,
        _decode_bytes(out_bytes),
        _decode_bytes(err_bytes),
        elapsed,
    )


def web_search(query: str, api_key: str) -> ToolResult:
    started = time.perf_counter()
    if not api_key:
        return ToolResult(
            action="search",
            payload=query,
            ok=False,
            stdout="",
            stderr="未配置 Tavily Search Key",
            elapsed=time.perf_counter() - started,
        )

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "search_depth": "basic"},
            timeout=12,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        if not results:
            return ToolResult(
                action="search",
                payload=query,
                ok=True,
                stdout="未找到相关结果",
                stderr="",
                elapsed=time.perf_counter() - started,
            )

        lines = []
        for item in results[:3]:
            title = item.get("title", "无标题")
            content = item.get("content", "")[:200]
            lines.append(f"- **{title}**: {content}")
        return ToolResult(
            action="search",
            payload=query,
            ok=True,
            stdout="\n".join(lines),
            stderr="",
            elapsed=time.perf_counter() - started,
        )
    except Exception as exc:
        return ToolResult(
            action="search",
            payload=query,
            ok=False,
            stdout="",
            stderr=str(exc),
            elapsed=time.perf_counter() - started,
        )


def truncate_for_context(text: str, limit: int = MAX_OBSERVATION_CHARS) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[上下文输出已截断]"
