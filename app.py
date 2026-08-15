import datetime
import queue
import threading
import time

import streamlit as st

from mingagent.config import (
    APP_NAME,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_STEP_LIMIT,
    MAX_STEP_LIMIT,
    MODEL_OPTIONS,
)
from mingagent.environment import detect_environment
from mingagent.history import load_history, load_snapshot
from mingagent.memory import delete_expertise, load_expertise
from mingagent.runner import agent_loop_worker
from mingagent.secrets import clear_api_key, load_api_key, save_api_key
from mingagent.settings import ACCENT_OPTIONS, THEME_OPTIONS, load_settings, save_settings
from mingagent.ui import (
    inject_css,
    inject_keyboard_shortcuts,
    render_alert,
    render_danger_card,
    render_empty_state,
    render_events,
    render_live_thought,
    render_live_tool,
    render_progress,
    render_topbar,
)


st.set_page_config(
    page_title=APP_NAME,
    layout="wide",
    initial_sidebar_state="expanded",
)


DEFAULTS = {
    "events": [],
    "step_limit": DEFAULT_STEP_LIMIT,
    "search_enabled": True,
    "safemode": True,
    "pending_prompt": None,
    "view_snapshot": None,
    "cfg_remember_key": False,
    "_saved_key": "",
    "cfg_apikey": "",
    "cfg_baseurl": DEFAULT_BASE_URL,
    "cfg_model_choice": DEFAULT_MODEL,
    "cfg_custom_model": DEFAULT_MODEL,
    "cfg_searchkey": "",
    "history": [],
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value
    stored_key = load_api_key()
    if not st.session_state.get("cfg_apikey"):
        st.session_state.cfg_apikey = stored_key
    if "cfg_remember_key" not in st.session_state:
        st.session_state.cfg_remember_key = bool(stored_key)
    if "history_loaded" not in st.session_state:
        st.session_state.history = load_history()
        st.session_state.history_loaded = True
    if "cfg_theme" not in st.session_state:
        prefs = load_settings()
        theme_key = next((k for k, v in THEME_OPTIONS.items() if v == prefs["theme"]), "暗色")
        accent_key = next((k for k, v in ACCENT_OPTIONS.items() if v == prefs["accent"]), "终端白")
        st.session_state.cfg_theme = theme_key
        st.session_state.cfg_accent = accent_key
        st.session_state._saved_prefs = (theme_key, accent_key)


def reset_session() -> None:
    rs = st.session_state.get("run_state")
    if rs is not None:
        rs["cancel"].set()
    st.session_state.run_state = None
    st.session_state.events = []
    st.session_state.view_snapshot = None


def summarize_task(text: str, limit: int = 60) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def resolved_model_name() -> str:
    choice = st.session_state.get("cfg_model_choice", DEFAULT_MODEL)
    if choice == "自定义":
        return st.session_state.get("cfg_custom_model", DEFAULT_MODEL)
    return choice


def snapshot_config() -> dict:
    return {
        "api_key": st.session_state.get("cfg_apikey", ""),
        "base_url": st.session_state.get("cfg_baseurl", DEFAULT_BASE_URL),
        "model": resolved_model_name(),
        "search_key": st.session_state.get("cfg_searchkey", ""),
        "search_enabled": st.session_state.get("search_enabled", True),
        "safe_mode": st.session_state.get("safemode", True),
        "step_limit": int(st.session_state.get("step_limit", DEFAULT_STEP_LIMIT)),
        "env_info": detect_environment(),
    }


def submit_prompt(prompt: str, resume=None) -> None:
    prompt = prompt.strip()
    if not prompt:
        return
    if not st.session_state.get("cfg_apikey", ""):
        st.session_state.pending_prompt = (prompt, resume)
        st.rerun()

    old = st.session_state.get("run_state")
    if old is not None:
        old["cancel"].set()

    resume_events = resume.get("events", []) if resume else []
    resume_messages = resume.get("messages", []) if resume else []
    st.session_state.view_snapshot = None

    rs = {
        "task": summarize_task(prompt),
        "events": list(resume_events) + [{"type": "user", "content": prompt}],
        "log": list(resume_events) + [{"type": "user", "content": prompt}],
        "inbox": queue.Queue(),
        "live": {"text": "", "tool": None, "step": 0},
        "pending": None,
        "cancel": threading.Event(),
        "running": True,
        "rerun_done": False,
        "toasted": False,
        "limit": int(st.session_state.get("step_limit", DEFAULT_STEP_LIMIT)),
    }
    st.session_state.run_state = rs
    threading.Thread(
        target=agent_loop_worker,
        args=(rs, prompt, snapshot_config(), resume_messages),
        daemon=True,
    ).start()
    st.rerun()


def render_run_state(rs: dict) -> None:
    inbox = rs["inbox"]
    while True:
        try:
            event = inbox.get_nowait()
        except queue.Empty:
            break
        rs["events"].append(event)

    render_events(rs["events"])

    live = rs["live"]
    if rs["running"] and live.get("step"):
        render_progress(live["step"], rs.get("limit", 1))
    if live.get("text"):
        render_live_thought(live["text"])
    if live.get("tool"):
        render_live_tool(live["tool"])

    pending = rs.get("pending")
    if pending:
        choice = render_danger_card(
            pending["parsed"],
            pending.get("reason", ""),
            pending.get("safe_mode", True),
        )
        if choice == "confirm":
            pending["decision"] = "confirmed"
            pending["event"].set()
            st.rerun()
        elif choice == "cancel":
            pending["decision"] = "cancelled"
            pending["event"].set()
            st.rerun()

    if not rs["running"] and not rs.get("rerun_done"):
        rs["rerun_done"] = True
        if not rs.get("toasted"):
            rs["toasted"] = True
            finals = [e for e in rs["events"] if e.get("type") == "final"]
            if finals:
                kind = finals[-1].get("kind", "success")
                toast_text = {
                    "success": "任务完成 ✅",
                    "error": "任务失败 ❌",
                    "stopped": "任务已停止",
                }.get(kind)
                if toast_text:
                    st.toast(toast_text)
        st.session_state.history = load_history()
        st.rerun()


def current_status(rs) -> tuple[str, str]:
    if rs and rs["running"]:
        return "Running", "running"
    if rs and rs["events"]:
        final_events = [e for e in rs["events"] if e.get("type") == "final"]
        if final_events:
            kind = final_events[-1].get("kind", "success")
            if kind == "error":
                return "Attention", "attention"
            if kind == "stopped":
                return "Stopped", "ready"
            return "Completed", "completed"
    return "Ready", "ready"


def status_label(status: str) -> str:
    return {
        "completed": "已完成",
        "error": "失败",
        "stopped": "已停止",
    }.get(status, status)


def format_time(ts) -> str:
    if not ts:
        return ""
    dt = datetime.datetime.fromtimestamp(ts)
    diff = datetime.datetime.now() - dt
    if diff.days <= 0:
        if diff.seconds < 60:
            return "刚刚"
        if diff.seconds < 3600:
            return f"{diff.seconds // 60}m"
        return f"{diff.seconds // 3600}h"
    if diff.days == 1:
        return "昨天"
    return dt.strftime("%m-%d")


init_state()

theme_key = st.session_state.get("cfg_theme", "暗色")
accent_key = st.session_state.get("cfg_accent", "终端白")
inject_css(THEME_OPTIONS.get(theme_key, "dark"), ACCENT_OPTIONS.get(accent_key, "#F5F5F5"))
inject_keyboard_shortcuts()


with st.sidebar:
    if st.button("新建任务", use_container_width=True, key="new_task"):
        reset_session()
        st.rerun()

    st.markdown('<div class="side-section">最近任务</div>', unsafe_allow_html=True)
    history = st.session_state.get("history", [])
    if not history:
        st.markdown('<div class="side-empty">暂无任务</div>', unsafe_allow_html=True)
    else:
        for item in history[:20]:
            title = item.get("title") or "Untitled"
            status = item.get("status", "completed")
            if st.button(title, key=f"hist_{item.get('id')}", use_container_width=True):
                snapshot = load_snapshot(str(item.get("id", "")))
                if snapshot:
                    st.session_state.view_snapshot = {
                        "title": title,
                        "events": snapshot.get("events", []),
                        "messages": snapshot.get("messages", []),
                    }
                    st.rerun()
                else:
                    submit_prompt(title)
            st.markdown(
                f'<div class="hist-meta {status}">{status_label(status)} · {format_time(item.get("ts"))}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="side-section">设置</div>', unsafe_allow_html=True)
    api_key = st.text_input("LLM API Key", type="password", key="cfg_apikey")
    remember_key = st.checkbox("在本机记住 Key（明文保存到项目目录）", key="cfg_remember_key")
    if remember_key:
        if st.session_state.get("_saved_key") != api_key:
            st.session_state._saved_key = api_key
            save_api_key(api_key)
    else:
        if st.session_state.get("_saved_key"):
            st.session_state._saved_key = ""
            clear_api_key()
    st.text_input("API URL", key="cfg_baseurl")
    model_choice = st.selectbox("模型", MODEL_OPTIONS, key="cfg_model_choice")
    if model_choice == "自定义":
        st.text_input("模型 ID", key="cfg_custom_model")
    st.slider("最大步数", 1, MAX_STEP_LIMIT, key="step_limit")
    st.toggle("联网搜索", key="search_enabled")
    st.toggle("安全模式", key="safemode")
    st.caption("仅只读白名单自动执行，其余操作需确认。")
    st.text_input("Tavily Key", type="password", key="cfg_searchkey")

    st.markdown('<div class="side-section">外观</div>', unsafe_allow_html=True)
    theme_label = st.selectbox("主题", list(THEME_OPTIONS), key="cfg_theme")
    accent_label = st.selectbox("强调色", list(ACCENT_OPTIONS), key="cfg_accent")
    if st.session_state.get("_saved_prefs") != (theme_label, accent_label):
        st.session_state._saved_prefs = (theme_label, accent_label)
        save_settings(THEME_OPTIONS[theme_label], ACCENT_OPTIONS[accent_label])

    with st.expander("经验库"):
        expertise = load_expertise()
        if not expertise:
            st.markdown('<div class="side-empty">暂无经验</div>', unsafe_allow_html=True)
        else:
            for index, item in enumerate(expertise):
                cols = st.columns([5, 1])
                cols[0].caption(f"{item.get('task', '')} → {item.get('cmd', '')[:36]}")
                if cols[1].button("🗑", key=f"exp_del_{index}", help="删除该经验"):
                    delete_expertise(item.get("cmd", ""))
                    st.rerun()

    rs_sidebar = st.session_state.get("run_state")
    if rs_sidebar is not None and rs_sidebar["running"]:
        if st.button("停止", key="stop_run", use_container_width=True):
            rs_sidebar["cancel"].set()
            st.rerun()


api_key = st.session_state.get("cfg_apikey", "")
rs = st.session_state.get("run_state")

status_text, status_class = current_status(rs)
render_topbar(status_text, status_class, resolved_model_name())

if not api_key:
    render_alert("未配置 API Key：在侧边栏完成设置。", "info")
    st.stop()

if rs is not None:
    render_run_state(rs)
    if rs["running"]:
        # 轮询刷新：工作线程在后台跑，主线程每 0.4s 重绘一次
        time.sleep(0.4)
        st.rerun()
else:
    view = st.session_state.get("view_snapshot")
    if view is not None:
        render_events(view.get("events", []))
        st.info(
            f"正在查看历史会话「{view.get('title', '')}」。在下方输入新指令即可基于该会话继续。"
        )
    elif not st.session_state.events:
        example = render_empty_state()
        if example:
            submit_prompt(example)

if pending := st.session_state.get("pending_prompt"):
    st.session_state.pending_prompt = None
    submit_prompt(pending[0], resume=pending[1])

if prompt := st.chat_input("Ask the agent to do something…"):
    submit_prompt(prompt, resume=st.session_state.get("view_snapshot"))
