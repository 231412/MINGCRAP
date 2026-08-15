import html
import itertools

import streamlit as st

from .security import read_recent_audit


_code_block_ids = itertools.count()


DARK_THEME_VARS = """
    --bg: #0A0A0A;
    --surface: #111111;
    --surface-2: #161616;
    --surface-hover: #1B1B1B;
    --sidebar-bg: #0D0D0D;
    --border: rgba(255, 255, 255, 0.08);
    --border-strong: rgba(255, 255, 255, 0.14);
    --text: #F5F5F5;
    --text-muted: #A3A3A3;
    --text-subtle: #6E6E76;
    --accent-fg: #0A0A0A;
    --topbar-bg: rgba(10, 10, 10, 0.92);
    --code-head-bg: #131313;
    --success: #3FB950;
    --warning: #D29922;
    --error: #F85149;
    --error-soft: rgba(248, 81, 73, 0.06);
    --error-border: rgba(248, 81, 73, 0.40);
    --error-text: #FF8A84;
    --info: #9AA0A6;
"""

LIGHT_THEME_VARS = """
    --bg: #F7F7F8;
    --surface: #FFFFFF;
    --surface-2: #EFEFF1;
    --surface-hover: #E7E7EA;
    --sidebar-bg: #F2F2F4;
    --border: rgba(0, 0, 0, 0.10);
    --border-strong: rgba(0, 0, 0, 0.18);
    --text: #17181A;
    --text-muted: #55575C;
    --text-subtle: #8B8E96;
    --accent-fg: #0A0A0A;
    --topbar-bg: rgba(247, 247, 248, 0.92);
    --code-head-bg: #F2F2F4;
    --success: #1A7F37;
    --warning: #9A6700;
    --error: #CF222E;
    --error-soft: rgba(207, 34, 46, 0.06);
    --error-border: rgba(207, 34, 46, 0.35);
    --error-text: #B62324;
    --info: #57606A;
"""


CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
    {theme_vars}
    --accent: {accent};
    --radius: 8px;
    --radius-sm: 6px;
}}

html, body, [class*="st-"] {{
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}}

.stApp {{
    background: var(--bg);
    color: var(--text);
}}

header[data-testid="stHeader"] {{
    display: none;
}}

#MainMenu, footer {{
    visibility: hidden;
    height: 0;
}}

section[data-testid="stSidebar"] {{
    width: 240px !important;
    min-width: 240px !important;
    max-width: 240px !important;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
}}

section[data-testid="stSidebar"] > div {{
    padding: 14px 12px;
}}

[data-testid="stSidebarResizeHandle"],
button[data-testid="stSidebarCollapseButton"] {{
    display: none !important;
}}

.side-section {{
    margin: 18px 0 7px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}

.side-empty {{
    color: var(--text-subtle);
    font-size: 12px;
    padding: 6px 2px;
}}

.hist-meta {{
    margin: -6px 2px 10px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
}}

.hist-meta.completed {{
    color: var(--success);
}}

.hist-meta.error {{
    color: var(--error);
}}

.hist-meta.stopped {{
    color: var(--text-subtle);
}}

.block-container {{
    position: relative;
    max-width: 1040px;
    padding: 0 2rem 11rem;
    margin: 0 auto;
}}

.topbar {{
    position: sticky;
    top: 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: 10px;
    height: 50px;
    margin: 0 -2rem 18px;
    padding: 0 2rem;
    background: var(--topbar-bg);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(8px);
}}

.brand-mark {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border: 1px solid var(--border-strong);
    border-radius: 5px;
    background: var(--surface);
    color: var(--text);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    font-weight: 600;
    flex: 0 0 auto;
}}

.brand-name {{
    color: var(--text);
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.02em;
}}

.top-status {{
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-muted);
    font-size: 12px;
}}

.top-status .dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--text-subtle);
}}

.top-status.running .dot {{
    background: var(--warning);
    animation: pulse 1.6s ease-in-out infinite;
}}

.top-status.completed .dot {{
    background: var(--success);
}}

.top-status.attention .dot {{
    background: var(--error);
}}

.top-model {{
    margin-left: auto;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12px;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 0.35; }}
    50% {{ opacity: 1; }}
}}

.progress-rail {{
    height: 2px;
    margin: -10px 0 16px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
}}

.progress-fill {{
    height: 100%;
    background: var(--accent);
    border-radius: 2px;
    transition: width 300ms ease;
}}

.progress-caption {{
    margin: -10px 0 14px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 10px;
    letter-spacing: 0.08em;
    text-align: right;
}}

.msg-label {{
    margin: 24px 0 6px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}}

.user-cmd {{
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 14px;
    line-height: 1.6;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
}}

.intent {{
    color: var(--text-muted);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12.5px;
    line-height: 1.6;
    white-space: pre-wrap;
}}

.tool-module {{
    margin: 10px 0 16px;
    padding-left: 12px;
    border-left: 2px solid var(--border-strong);
}}

.tool-module.success {{
    border-left-color: var(--success);
}}

.tool-module.error {{
    border-left-color: var(--error);
}}

.tool-module.running {{
    border-left-color: var(--warning);
}}

.tool-module summary {{
    list-style: none;
    cursor: pointer;
    user-select: none;
}}

.tool-module summary::-webkit-details-marker {{
    display: none;
}}

.tool-module summary::before {{
    content: "▸";
    display: inline-block;
    margin-right: 8px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    transition: transform 150ms ease;
}}

.tool-module[open] summary::before {{
    transform: rotate(90deg);
}}

.tool-head {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: var(--text);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
    letter-spacing: 0.04em;
    padding: 2px 0;
}}

.tool-seq {{
    color: var(--text-subtle);
    font-variant-numeric: tabular-nums;
}}

.tool-name {{
    text-transform: uppercase;
    letter-spacing: 0.08em;
}}

.tool-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--text-subtle);
    flex: 0 0 auto;
}}

.tool-module.success .tool-dot {{
    background: var(--success);
}}

.tool-module.error .tool-dot {{
    background: var(--error);
}}

.tool-module.running .tool-dot {{
    background: var(--warning);
    animation: pulse 1.6s ease-in-out infinite;
}}

.tool-elapsed {{
    margin-left: auto;
    color: var(--text-subtle);
    font-variant-numeric: tabular-nums;
}}

.tool-body {{
    margin-top: 8px;
    padding-right: 12px;
}}

.tool-label {{
    margin: 12px 0 6px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

.fold-note {{
    margin: 10px 0 2px;
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
}}

.code-shell {{
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    overflow: hidden;
}}

.code-head {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    border-bottom: 1px solid var(--border);
    background: var(--code-head-bg);
}}

.code-lang {{
    color: var(--text-subtle);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}

.code-copy {{
    padding: 2px 7px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-family: "Inter", sans-serif;
    font-size: 10px;
    transition: color 150ms ease, border-color 150ms ease;
}}

.code-copy:hover {{
    color: var(--text);
    border-color: var(--border-strong);
}}

.code-shell pre {{
    margin: 0;
    padding: 14px;
    overflow: auto;
    white-space: pre;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12.5px;
    line-height: 1.58;
    color: var(--text);
    tab-size: 2;
}}

.result-rule {{
    height: 1px;
    margin: 20px 0 14px;
    background: var(--border);
}}

.done-line {{
    margin: 8px 0 20px;
    color: var(--success);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 11px;
}}

.done-line.error {{
    color: var(--error);
}}

.done-line.muted {{
    color: var(--text-subtle);
}}

[data-testid="stMarkdownContainer"] p {{
    margin: 0 0 10px;
    line-height: 1.7;
}}

[data-testid="stMarkdownContainer"] strong {{
    color: var(--text);
    font-weight: 600;
}}

[data-testid="stMarkdownContainer"] ul,
[data-testid="stMarkdownContainer"] ol {{
    margin: 0 0 12px;
    padding-left: 1.25rem;
}}

[data-testid="stMarkdownContainer"] li {{
    margin: 3px 0;
}}

[data-testid="stMarkdownContainer"] code {{
    padding: 1px 5px;
    border: 1px solid var(--border);
    border-radius: 5px;
    background: var(--surface);
    color: var(--text);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 0.9em;
}}

.empty-state {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 56vh;
    text-align: center;
}}

.empty-mark {{
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    margin-bottom: 14px;
    border: 1px solid var(--border-strong);
    border-radius: var(--radius);
    background: var(--surface);
    color: var(--text);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 15px;
    font-weight: 600;
}}

.empty-title {{
    margin: 0 0 6px;
    color: var(--text);
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.01em;
}}

.empty-subtitle {{
    margin: 0 0 24px;
    color: var(--text-muted);
    font-size: 13px;
}}

.alert {{
    margin: 18px 0;
    padding: 11px 13px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--surface);
    color: var(--text-muted);
    font-size: 13px;
}}

.alert.info {{
    border-color: var(--border-strong);
    color: var(--text-muted);
}}

.alert.error {{
    border-color: var(--error-border);
    background: var(--error-soft);
    color: var(--error-text);
}}

.danger-card {{
    margin: 10px 0 18px;
    padding: 14px;
    border: 1px solid var(--error-border);
    border-radius: var(--radius);
    background: var(--error-soft);
}}

.danger-title {{
    margin-bottom: 7px;
    color: var(--error-text);
    font-size: 13px;
    font-weight: 600;
}}

.danger-head {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.danger-head .danger-title {{
    margin-bottom: 0;
}}

.danger-tag {{
    padding: 2px 7px;
    border: 1px solid var(--error-border);
    border-radius: var(--radius-sm);
    color: var(--error-text);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 10px;
    letter-spacing: 0.08em;
}}

.danger-copy {{
    margin: 8px 0 0;
    color: var(--text-muted);
    font-size: 12px;
    line-height: 1.6;
}}

.danger-command {{
    margin-top: 10px;
    padding: 11px 13px;
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12px;
    white-space: pre;
}}

.stButton > button,
.stDownloadButton > button {{
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: border-color 150ms ease, background 150ms ease, color 150ms ease;
}}

.stButton > button:hover,
.stDownloadButton > button:hover {{
    background: var(--surface-hover);
    border-color: var(--border-strong);
    color: var(--text);
}}

.stButton > button[kind="primary"] {{
    background: var(--accent);
    border-color: var(--accent);
    color: var(--accent-fg);
}}

.stButton > button[kind="primary"]:hover {{
    filter: brightness(1.1);
    color: var(--accent-fg);
}}

.stTextInput input,
.stTextArea textarea,
[data-baseweb="select"] > div {{
    background: var(--surface);
    color: var(--text);
    border-color: var(--border);
    border-radius: var(--radius);
}}

.stTextInput input:focus,
.stTextArea textarea:focus {{
    border-color: var(--border-strong);
    box-shadow: 0 0 0 1px var(--border);
}}

.stSelectbox [data-baseweb="select"] > div {{
    background: var(--surface);
    border-color: var(--border);
}}

[data-testid="stChatInput"] {{
    position: fixed;
    bottom: 18px;
    left: 240px;
    right: 0;
    max-width: 760px;
    margin-left: auto;
    margin-right: auto;
    z-index: 40;
    display: flex;
    align-items: center;
    padding: 4px 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}}

[data-testid="stChatInput"]::before {{
    content: ">_";
    color: var(--text-muted);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 13px;
    margin: 0 8px 0 2px;
}}

[data-testid="stChatInput"]:focus-within {{
    border-color: var(--border-strong);
    box-shadow: 0 0 0 1px var(--border);
}}

[data-testid="stChatInput"] textarea {{
    background: transparent;
    color: var(--text);
    border: 0;
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 13.5px;
    line-height: 1.6;
    padding: 8px 4px;
}}

[data-testid="stChatInput"] textarea::placeholder {{
    color: var(--text-subtle);
}}

[data-testid="stChatInput"] button {{
    background: transparent;
    border: 0;
    color: var(--text-muted);
}}

@media (max-width: 768px) {{
    section[data-testid="stSidebar"] {{
        display: none !important;
    }}

    .block-container {{
        padding-left: 1rem;
        padding-right: 1rem;
        padding-bottom: 11rem;
    }}

    .topbar {{
        margin-left: -1rem;
        margin-right: -1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    [data-testid="stChatInput"] {{
        left: 12px;
        right: 12px;
    }}
}}
"""


def inject_css(theme: str = "dark", accent: str = "#F5F5F5") -> None:
    theme_vars = LIGHT_THEME_VARS if theme == "light" else DARK_THEME_VARS
    st.markdown(
        f"<style>{CSS.format(theme_vars=theme_vars, accent=accent)}</style>",
        unsafe_allow_html=True,
    )


def inject_keyboard_shortcuts() -> None:
    st.html(
        """
        <script>
        (() => {
            if (window.__mingagentKeys) return;
            window.__mingagentKeys = true;
            const handler = (e) => {
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    const btn = document.querySelector('[data-testid="stChatInputSubmitButton"]');
                    if (btn) { e.preventDefault(); btn.click(); }
                } else if (e.key === 'Escape') {
                    const stop = Array.from(document.querySelectorAll('button')).find(
                        (b) => b.textContent.trim() === '停止'
                    );
                    if (stop) { e.preventDefault(); stop.click(); }
                }
            };
            document.addEventListener('keydown', handler, true);
        })();
        </script>
        """,
        width="stretch",
        unsafe_allow_javascript=True,
    )


def render_topbar(status_text: str, status_class: str, model_name: str) -> None:
    st.markdown(
        f"""
        <div class="topbar">
            <span class="brand-mark">>_</span>
            <span class="brand-name">MINGAGENT</span>
            <span class="top-status {status_class}"><span class="dot"></span>{html.escape(status_text)}</span>
            <span class="top-model">{html.escape(model_name)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress(current: int, total: int) -> None:
    if total <= 0:
        return
    pct = min(100, max(0, round(current / total * 100)))
    st.markdown(
        f"""
        <div class="progress-rail"><div class="progress-fill" style="width:{pct}%"></div></div>
        <div class="progress-caption">STEP {current}/{total}</div>
        """,
        unsafe_allow_html=True,
    )


def render_live_thought(text: str) -> None:
    """渲染当前步骤的流式思考文本（带光标）。"""
    st.markdown(
        f'<div class="msg-label">PLANNING</div><div class="intent">{html.escape(text)}▌</div>',
        unsafe_allow_html=True,
    )


def render_live_tool(action: str) -> None:
    """渲染执行中的工具模块（脉冲状态点）。"""
    labels = {"cmd": "TERMINAL", "python": "PYTHON", "search": "SEARCH"}
    st.markdown(
        f"""
        <div class="tool-module running">
            <div class="tool-head">
                <span class="tool-dot"></span>
                <span class="tool-name">{labels.get(action, action.upper())}</span>
            </div>
            <div class="fold-note">执行中…</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> str | None:
    examples = [
        ("📂", "分析当前项目"),
        ("🧹", "整理下载文件夹"),
        ("🔍", "查找大文件"),
        ("🧪", "运行测试套件"),
    ]
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-mark">>_</div>
            <div class="empty-title">LOCAL AGENT</div>
            <div class="empty-subtitle">What should I work on?</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    clicked = None
    for index, (icon, label) in enumerate(examples):
        if cols[index].button(f"{icon}  {label}", key=f"example_{index}", use_container_width=True):
            clicked = label
    return clicked


def render_events(events: list[dict]) -> None:
    tool_seq = 0
    for event in events:
        event_type = event.get("type")

        if event_type == "user":
            content = html.escape(event.get("content", ""))
            st.markdown('<div class="msg-label">USER</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="user-cmd">{content}</div>', unsafe_allow_html=True)

        elif event_type == "thought":
            thought = html.escape(event.get("content", ""))
            st.markdown('<div class="msg-label">PLANNING</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="intent">{thought}</div>', unsafe_allow_html=True)

        elif event_type == "tool":
            tool_seq += 1
            render_tool_step(step=event, seq=tool_seq)

        elif event_type == "final":
            st.markdown('<div class="msg-label">RESULT</div>', unsafe_allow_html=True)
            st.markdown(event.get("content", ""))
            kind = event.get("kind", "success")
            if kind == "error":
                marker = "FAILED"
                marker_class = "error"
            elif kind == "stopped":
                marker = "STOPPED"
                marker_class = "muted"
            else:
                marker = "COMPLETED"
                marker_class = ""
            st.markdown(
                f'<div class="done-line {marker_class}">{marker}</div>',
                unsafe_allow_html=True,
            )


def _preview_lines(text: str, max_lines: int = 30) -> tuple[str, bool]:
    lines = text.splitlines() or [text]
    if len(lines) <= max_lines:
        return text, False
    return "\n".join(lines[:max_lines]), True


def code_block_html(code: str, language: str = "text", max_height: int = 300) -> str:
    code = code or ""
    safe_code = html.escape(code, quote=True)
    block_id = f"code-block-{next(_code_block_ids)}"
    return f"""
    <div id="{block_id}" class="code-shell">
        <div class="code-head">
            <span class="code-lang">{html.escape(language)}</span>
            <button class="code-copy" type="button">Copy</button>
        </div>
        <pre style="max-height:{max_height}px;"><code>{safe_code}</code></pre>
    </div>
    <script>
        (() => {{
            const shell = document.getElementById('{block_id}');
            if (!shell || shell.dataset.bound) return;
            shell.dataset.bound = '1';
            const button = shell.querySelector('.code-copy');
            const target = shell.querySelector('code');
            if (!button || !target) return;
            button.addEventListener('click', async () => {{
                const text = target.innerText;
                try {{
                    await navigator.clipboard.writeText(text);
                    button.textContent = 'Copied';
                }} catch (err) {{
                    const area = document.createElement('textarea');
                    area.value = text;
                    document.body.appendChild(area);
                    area.select();
                    document.execCommand('copy');
                    document.body.removeChild(area);
                    button.textContent = 'Copied';
                }}
                setTimeout(() => {{ button.textContent = 'Copy'; }}, 1200);
            }});
        }})();
    </script>
    """


def code_block(code: str, language: str = "text", max_height: int = 300) -> None:
    st.html(
        code_block_html(code, language, max_height),
        width="stretch",
        unsafe_allow_javascript=True,
    )


def render_tool_step(step: dict, seq: int) -> None:
    action = step.get("action", "cmd")
    labels = {"cmd": "TERMINAL", "python": "PYTHON", "search": "SEARCH"}
    status = step.get("status", "success")
    elapsed = float(step.get("elapsed", 0.0))
    payload = step.get("payload", "")
    output = step.get("output", "")
    truncated = bool(step.get("truncated", False))

    status_class = "success" if status == "success" else "error"
    head_label = labels.get(action, action.upper())

    if action == "search":
        # 搜索步骤平铺渲染：SOURCES 需要保留 Markdown 格式
        st.markdown(
            f"""
            <div class="tool-module {status_class}">
                <div class="tool-head">
                    <span class="tool-dot"></span>
                    <span class="tool-seq">#{seq}</span>
                    <span class="tool-name">{head_label}</span>
                    <span class="tool-elapsed">{elapsed:.1f}s</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="tool-label">QUERY</div>', unsafe_allow_html=True)
        code_block(payload, language="text", max_height=160)
        if output:
            st.markdown('<div class="tool-label">SOURCES</div>', unsafe_allow_html=True)
            st.markdown(output)
        return

    # cmd / python：可折叠的时间线步骤
    preview, folded = _preview_lines(output, max_lines=30)
    open_attr = "" if (folded or truncated) else "open"
    body_parts = [
        '<div class="tool-label">COMMAND</div>' if action == "cmd" else '<div class="tool-label">CODE</div>',
        code_block_html(payload, language="powershell" if action == "cmd" else "python"),
    ]
    if output:
        shown = output if folded else preview
        body_parts.extend(
            [
                '<div class="tool-label">OUTPUT</div>',
                code_block_html(shown, language="text", max_height=640 if folded else 320),
            ]
        )
        if folded:
            body_parts.append(
                f'<div class="fold-note">已折叠 {len(output.splitlines())} 行输出</div>'
            )
        if truncated and not folded:
            body_parts.append('<div class="fold-note">输出已截断（超出工具上限）</div>')

    st.html(
        f"""
        <details class="tool-module {status_class}" {open_attr}>
            <summary class="tool-head">
                <span class="tool-dot"></span>
                <span class="tool-seq">#{seq}</span>
                <span class="tool-name">{head_label}</span>
                <span class="tool-elapsed">{elapsed:.1f}s</span>
            </summary>
            <div class="tool-body">
                {"".join(body_parts)}
            </div>
        </details>
        """,
        width="stretch",
        unsafe_allow_javascript=True,
    )


def render_danger_card(parsed: dict, reason: str = "", safe_mode: bool = True) -> str | None:
    action = parsed.get("action", "cmd")
    action_label = {"cmd": "TERMINAL", "python": "PYTHON", "search": "SEARCH"}.get(
        action, action.upper()
    )
    payload = parsed.get("payload", "")
    mode_note = (
        "安全模式：该操作超出只读白名单，需要人工确认。"
        if safe_mode
        else "自动模式：该操作命中危险规则，需要人工确认。"
    )
    reason_html = f'<div class="danger-copy">{html.escape(reason)}</div>' if reason else ""
    st.markdown(
        f"""
        <div class="danger-card">
            <div class="danger-head">
                <span class="danger-title">危险操作待确认</span>
                <span class="danger-tag">{action_label}</span>
            </div>
            <div class="danger-copy">{mode_note}</div>
            {reason_html}
            <div class="danger-command">{html.escape(payload)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("最近审计记录", expanded=False):
        records = read_recent_audit(5)
        if not records:
            st.markdown('<div class="side-empty">暂无审计记录</div>', unsafe_allow_html=True)
        else:
            for record in records:
                line = (
                    f"`{record.get('event', '?')}` · `{record.get('action', '?')}` · "
                    f"{html.escape(str(record.get('payload', ''))[:60])}"
                )
                if record.get("decision"):
                    line += f" → {html.escape(str(record['decision']))}"
                st.markdown(line)

    left, right = st.columns([1, 1])
    if left.button("确认执行", key="confirm_danger", type="primary", use_container_width=True):
        return "confirm"
    if right.button("取消", key="cancel_danger", use_container_width=True):
        return "cancel"
    return None


def render_alert(message: str, kind: str = "info") -> None:
    st.markdown(
        f'<div class="alert {kind}">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )
