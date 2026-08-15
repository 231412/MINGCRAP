import subprocess
import re
import streamlit as st
from openai import OpenAI
import locale

# 初始化
st.set_page_config(page_title="Mingcrap Agent", page_icon="🦀")
st.title("🦀 MINGCRAP V0.2")

#状态管理
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": """你是一个名为 Mingcrap 的高级 AI 终端助手。你可以通过操作本地电脑(Windows)来完成用户指令。

### 核心规则：
1. **思考与行动循环**：
   - 收到任务后，先进行分析，确定需要执行的操作。
   - 如果需要操作电脑，必须输出格式：`RUN_CMD: [具体的 Shell 命令]`。请不要在命令前后加任何反引号或代码块格式。
   - 每次只执行**一个**命令，并等待系统反馈结果。
   - 根据系统返回的“观测结果”决定下一步。

2. **自我修正**：
   - 如果命令报错，请分析原因（如路径空格、编码错误、PowerShell特有语法），并在下一轮尝试不同的解决方案。

3. **任务终结**：
   - 当任务彻底完成时，必须以 `FINISH: [总结性描述]` 开头。
"""
        }
    ]
if "pending_cmd" not in st.session_state:
    st.session_state.pending_cmd = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "step" not in st.session_state:
    st.session_state.step = 0

#侧边栏
with st.sidebar:
    st.header("⚙️ 配置中心")
    api_key = st.text_input("输入 API Key", type="password")
    base_url = st.text_input("API 基地 URL", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")

    st.divider()
    st.subheader("运行设置")
    max_steps = st.slider("最大决策步数", min_value=1, max_value=20, value=5)

if not api_key:
    st.warning("👈 请先在侧边栏输入 API Key 以启动 Mingcrap。")
    st.stop()

client = OpenAI(api_key=api_key, base_url=base_url)


#防上下文爆炸
def truncate_text(text, max_length=1500):
    if len(text) > max_length:
        return text[:max_length] + f"\n\n... [输出过长已被截断，省略了 {len(text) - max_length} 个字符]"
    return text


#命令执行
def decode_output(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        # 回退到系统默认编码
        encoding = locale.getpreferredencoding()
        return data.decode(encoding, errors='replace')

def execute_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, timeout=15)
        stdout = decode_output(result.stdout)
        stderr = decode_output(result.stderr)

        output_str = stdout
        if stderr:
            output_str += f"\n[标准错误输出]:\n{stderr}"

        if result.returncode == 0:
            return f"【执行成功】:\n{truncate_text(output_str)}"
        else:
            return f"【执行失败】(Exit Code {result.returncode}):\n{truncate_text(output_str)}"

    except subprocess.TimeoutExpired:
        return "【执行失败】: 命令执行超过 15 秒超时，已被强行中止。"
    except Exception as e:
        return f"【系统级错误】: {str(e)}"


#风险判定
def check_is_risky(command):
    danger_keywords = [
        "rm ", "del ", "format ", "shutdown ", ">", "mv ",
        "remove-item", "stop-computer", "clear-disk", "mkfs"
    ]
    return any(kw in command.lower() for kw in danger_keywords)


#渲染历史消息
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if st.session_state.pending_cmd:
    cmd = st.session_state.pending_cmd
    st.warning(f"⚠️ **高危操作拦截**：Mingcrap 申请执行以下命令，是否允许？\n\n`{cmd}`")

    col1, col2 = st.columns(2)
    if col1.button("✅ 允许执行", type="primary", use_container_width=True):
        obs = execute_command(cmd)
        st.session_state.messages.append({"role": "user", "content": f"SYSTEM_OBSERVATION: {obs}"})
        st.session_state.pending_cmd = None
        st.rerun()  #继续下一轮循环

    if col2.button("🚫 拒绝并取消", use_container_width=True):
        st.session_state.messages.append(
            {"role": "user", "content": "SYSTEM_OBSERVATION: 【操作取消】: 用户拒绝了该命令。"})
        st.session_state.pending_cmd = None
        st.rerun()  #拒绝,继续下一轮

    st.stop()

if prompt := st.chat_input("命令 Mingcrap 做点什么？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.is_running = True
    st.session_state.step = 0
    st.rerun()  #刷新页面

if st.session_state.is_running:
    if st.session_state.step < max_steps:
        with st.chat_message("assistant"):
            with st.status(f"思考与决策中 (Step {st.session_state.step + 1}/{max_steps})...", expanded=True) as status:

                response = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state.messages,
                    temperature=0.1,
                    stream=True
                )
                
                full_response = ""
                resp_placeholder = st.empty()
                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    full_response += content
                    resp_placeholder.markdown(full_response + "▌")
                resp_placeholder.markdown(full_response)

                if "RUN_CMD:" in full_response:
                    # 修正正则：提取 RUN_CMD: 后面的命令
                    match = re.search(r'RUN_CMD:\s*(.+)', full_response)
                    if match:
                        cmd = match.group(1).strip()
                        # 可选：去除可能的多余引号
                        cmd = cmd.strip('"').strip("'")

                        # 高危命令拦截
                        if check_is_risky(cmd):
                            st.session_state.pending_cmd = cmd
                            st.session_state.is_running = False  # 暂停自动循环
                            st.rerun()  # 触发用户确认界面
                        else:
                            # 直接执行命令
                            obs = execute_command(cmd)
                            st.session_state.messages.append({
                                "role": "user",
                                "content": f"SYSTEM_OBSERVATION: {obs}"
                            })
                            st.session_state.step += 1
                            st.rerun()  # 继续下一步决策
                    else:
                        # 如果正则匹配失败（格式错误），通知AI重新输出正确格式
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "SYSTEM_OBSERVATION: 无法解析命令格式，请按正确格式输出 RUN_CMD: [命令]"
                        })
                        st.rerun()
                    
