"""MINGAGENT 启动器：启动 Streamlit 服务并自动打开浏览器。

开发模式：
    python launcher.py [端口]

打包模式（PyInstaller 冻结后由 exe 直接执行）：
    - 数据目录自动切到 %APPDATA%\\MINGAGENT（见 mingagent/config.py）；
    - 通过进程内 bootstrap 启动 streamlit，不依赖系统 Python。
"""

import multiprocessing
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
DEFAULT_PORT = 8501


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_path() -> Path:
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return base / "app.py"
    return Path(__file__).resolve().parent / "app.py"


def find_free_port(start: int = DEFAULT_PORT, attempts: int = 20) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((HOST, port))
                return port
            except OSError:
                continue
    raise RuntimeError("未找到可用端口")


def _run_dev_mode(port: int) -> subprocess.Popen:
    args = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path()),
        "--server.headless",
        "true",
        "--server.address",
        HOST,
        "--server.port",
        str(port),
        "--browser.gatherUsageStats",
        "false",
    ]
    return subprocess.Popen(args)


def _run_frozen_mode(port: int) -> None:
    """冻结模式下进程内启动。注：本分支需在打包轮实测验证。"""
    from streamlit import config as st_config
    from streamlit.web import bootstrap

    st_config.set_option("server.headless", True)
    st_config.set_option("server.address", HOST)
    st_config.set_option("server.port", port)
    st_config.set_option("browser.gatherUsageStats", False)
    st_config.set_option("server.fileWatcherType", "none")  # 冻结环境禁用文件监听
    bootstrap.run(str(app_path()), False, [], {})


def _open_browser_when_ready(port: int, url: str) -> None:
    if os.environ.get("MINGAGENT_NO_BROWSER"):
        return
    for _ in range(120):
        try:
            with socket.create_connection((HOST, port), timeout=0.5):
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
                return
        except OSError:
            time.sleep(0.5)


def main(argv=None) -> int:
    multiprocessing.freeze_support()
    args = list(argv) if argv is not None else sys.argv[1:]
    port = int(args[0]) if args else find_free_port()
    url = f"http://{HOST}:{port}"

    threading.Thread(target=_open_browser_when_ready, args=(port, url), daemon=True).start()

    if is_frozen():
        print(f"MINGAGENT 已启动：{url}")
        _run_frozen_mode(port)
        return 0

    proc = _run_dev_mode(port)
    print(f"MINGAGENT 已启动：{url}（关闭本窗口即退出）")
    try:
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
