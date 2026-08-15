import subprocess
import json
import os
import tempfile
import requests
import streamlit as st
from openai import OpenAI

# =============================================================================
# CONSTANTS
# =============================================================================

EXPERTISE_FILE = "expertise.json"

ENV_TOOLS = [
    ("python", "python --version"),
    ("node", "node -v"),
    ("git", "git --version"),
    ("npm", "npm -v"),
]

# =============================================================================
# SESSION STATE INIT
# =============================================================================

st.set_page_config(
    page_title="Mingcrap Agent Pro",
    page_icon="🦀",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULTS = {
    "messages": [],
    "is_running": False,
    "step_count": 0,
    "step_limit": 10,
    "env_info": "",
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# =============================================================================
# HELPERS
# =============================================================================

def load_expertise():
    if not os.path.exists(EXPERTISE_FILE):
        return []
    try:
        with open(EXPERTISE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_expertise(task, cmd, result):
    if "执行成功" not in result or len(cmd) < 5:
        return
    data = load_expertise()
    if any(item.get("cmd") == cmd for item in data):
        return
    data.append({"task": task, "cmd": cmd})
    data = data[-20:]
    try:
        with open(EXPERTISE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


@st.cache_data(ttl=120)
def check_environment():
    """Detect installed tools; cached for 2 minutes."""
    installed = []
    for name, test_cmd in ENV_TOOLS:
        try:
            res = subprocess.run(
                test_cmd, shell=True, capture_output=True, text=True, timeout=3,
            )
            if res.returncode == 0:
                installed.append(name)
        except Exception:
            continue
    return ", ".join(installed) if installed else "仅基础 CMD 命令"


def web_search(query, api_key):
    """Tavily search."""
    if not api_key:
        return "[错误] 未配置 Tavily Search API Key"
    try:
        res = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": api_key, "query": query, "search_depth": "basic"},
            timeout=12,
        )
        results = res.json().get("results", [])
        if not results:
            return "[搜索] 未找到相关结果"
        lines = []
        for r in results[:3]:
            content = r.get("content", "")[:200]
            lines.append(f"- {r.get('title', '无标题')}: {content}")
        return "【互联网搜索结果】\n" + "\n".join(lines)
    except Exception as e:
        return f"[搜索失败] {e}"


def execute_python(code):
    """Execute Python snippet in a temp file — never overwrites project files."""
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".py", prefix="mc_py_", text=True)
        os.close(fd)
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(code)
        try:
            res = subprocess.run(
                ["python", tmp_path],
                capture_output=True, text=True, timeout=20,
            )
            out = res.stdout or ""
            err = res.stderr or ""
            return f"【Python 执行结果】\n{out}\n{err}".strip()
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
    except Exception as e:
        return f"【Python 报错】{e}"


def execute_cmd(command):
    """Execute a shell command with error capture."""
    try:
        res = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            errors="replace", timeout=30,
        )
        stdout = res.stdout.strip() if res.stdout else ""
        stderr = res.stderr.strip() if res.stderr else ""
        if stderr:
            return f"【CMD 执行结果】\n{stdout}\n[stderr] {stderr}"
        if stdout:
            return f"【CMD 执行成功】\n{stdout}"
        return "【CMD 执行完毕，无输出】"
    except subprocess.TimeoutExpired:
        return "[错误] 命令执行超时（30s）"
    except Exception as e:
        return f"[错误] 命令执行失败: {e}"


def build_system_prompt(env_info, expertise_data):
    expertise_lines = ""
    if expertise_data:
        lines = [
            f"- 任务: {e['task']} -> 命令: {e['cmd']}"
            for e in expertise_data
            if "task" in e and "cmd" in e
        ]
        expertise_lines = "\n".join(lines)

    return f"""你是一个高级 AI 终端助手 Mingcrap，运行在 Windows 上。

## 你的能力
1. 执行本地命令：输出 `RUN_CMD: <命令>`
2. 执行 Python 脚本：输出 `RUN_PY: <代码>`
3. 联网搜索：输出 `SEARCH_WEB: <关键词>`

## 当前环境
- 已安装工具：{env_info or "未知"}
- 操作系统：Windows

## 历史成功经验
{expertise_lines or "暂无"}

## 规则
- 每次只输出一个指令（RUN_CMD / RUN_PY / SEARCH_WEB）
- 代码不要用 markdown 代码块包裹，直接输出纯代码
- 完成任务后输出 `FINISH: <总结>`
- 遇到错误时，尝试分析原因并给出不同的解决方案
"""


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.header("⚙️ 配置")

    api_key = st.text_input("LLM API Key", type="password", key="cfg_apikey")
    search_key = st.text_input("Tavily Search Key", type="password", key="cfg_searchkey")
    base_url = st.text_input("API URL", value="https://api.deepseek.com", key="cfg_baseurl")
    model_name = st.text_input("模型", value="deepseek-chat", key="cfg_model")

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 检测环境"):
            check_environment.clear()
            st.session_state.env_info = check_environment()
            st.rerun()

    st.divider()

    env = st.session_state.env_info or check_environment()
    if not st.session_state.env_info:
        st.session_state.env_info = env
    st.caption(f"📍 已发现：{st.session_state.env_info}")

    st.divider()

    exp_data = load_expertise()
    with st.expander(f"📚 经验库（{len(exp_data)} 条）"):
        if exp_data:
            for item in exp_data:
                if "task" in item and "cmd" in item:
                    st.caption(item["task"])
                    st.code(item["cmd"], language="shell")
        else:
            st.caption("暂无经验记录")

    st.divider()

    st.session_state.step_limit = st.slider("最大步数", 1, 20, 10, key="cfg_steps")

    st.divider()

    if st.button("🗑️ 清空对话", use_container_width=True):
        for k in ["messages", "is_running", "step_count"]:
            st.session_state[k] = DEFAULTS[k]
        st.rerun()

    if st.session_state.is_running:
        if st.button("⏹️ 强制停止", use_container_width=True, type="primary"):
            st.session_state.is_running = False
            st.session_state.step_count = 0
            st.rerun()

# =============================================================================
# API KEY GUARD
# =============================================================================

if not api_key:
    st.title("🦀 MINGCRAP PRO")
    st.info("👈 请在侧边栏输入 LLM API Key")
    st.stop()

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

st.title("🦀 MINGCRAP PRO")

expertise_data = load_expertise()
sys_prompt = build_system_prompt(st.session_state.env_info, expertise_data)

if not st.session_state.messages or st.session_state.messages[0]["role"] != "system":
    st.session_state.messages.insert(0, {"role": "system", "content": sys_prompt})
else:
    st.session_state.messages[0]["content"] = sys_prompt

client = OpenAI(api_key=api_key, base_url=base_url)

# =============================================================================
# RENDER CHAT HISTORY (skip system message)
# =============================================================================

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =============================================================================
# CHAT INPUT
# =============================================================================

if prompt := st.chat_input("输入指令…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.is_running = True
    st.session_state.step_count = 0
    st.rerun()

# =============================================================================
# AGENT LOOP
# =============================================================================

if st.session_state.is_running:
    if st.session_state.step_count >= st.session_state.step_limit:
        st.warning(f"已达最大步数上限（{st.session_state.step_limit}），自动停止。")
        st.session_state.is_running = False
        st.stop()

    st.session_state.step_count += 1

    with st.chat_message("assistant"):
        step_label = f"步骤 {st.session_state.step_count}/{st.session_state.step_limit} · 思考中…"
        with st.status(step_label) as status_ctx:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state.messages,
                    temperature=0.1,
                )
            except Exception as e:
                st.error(f"LLM 调用失败: {e}")
                st.session_state.is_running = False
                st.stop()

            full_resp = response.choices[0].message.content
            st.markdown(full_resp)

            obs = ""
            current_cmd = ""

            if "RUN_CMD:" in full_resp:
                current_cmd = full_resp.split("RUN_CMD:", 1)[1].strip().split("\n")[0]
                obs = execute_cmd(current_cmd)

            elif "RUN_PY:" in full_resp:
                code = full_resp.split("RUN_PY:", 1)[1].strip()
                for fence in ("```python", "```py", "```"):
                    code = code.replace(fence, "")
                current_cmd = code.strip()
                obs = execute_python(current_cmd)

            elif "SEARCH_WEB:" in full_resp:
                query = full_resp.split("SEARCH_WEB:", 1)[1].strip().split("\n")[0]
                obs = web_search(query, search_key)

            if obs:
                st.code(obs, language="text")
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                st.session_state.messages.append({"role": "user", "content": f"SYSTEM_OBSERVATION: {obs}"})

                if "RUN_CMD:" in full_resp and "执行成功" in obs:
                    user_task = ""
                    for m in reversed(st.session_state.messages):
                        if m["role"] == "user" and not m["content"].startswith("SYSTEM_OBSERVATION"):
                            user_task = m["content"][:80]
                            break
                    save_expertise(user_task, current_cmd, obs)

                st.rerun()
            else:
                st.session_state.messages.append({"role": "assistant", "content": full_resp})
                st.session_state.is_running = False
                status_ctx.update(label="完成", state="complete")
