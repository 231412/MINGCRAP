import subprocess

import streamlit as st

from .config import ENV_TOOLS


@st.cache_data(ttl=120)
def detect_environment() -> str:
    installed = []
    for name, command in ENV_TOOLS:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=3,
            )
            if result.returncode == 0:
                installed.append(name)
        except Exception:
            continue
    return ", ".join(installed) if installed else "core"

