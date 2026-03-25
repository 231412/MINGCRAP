import subprocess
import tkinter as tk
from tkinter import messagebox

import streamlit as st
from openai import OpenAI

#初始化

st.set_page_config(page_title="Mingcrap Agent", page_icon="🦀")
st.title("🦀 MINGCRAP")

#API

with st.sidebar:
    st.header("配置中心")
    api_key = st.text_input("输入 API Key", type="password")
    base_url = st.text_input("API 基地 URL", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")
    st.info("Mingcrap 会在执行危险操作前弹出本地窗口请求授权。")

if not api_key:
    st.warning("请先在侧边栏输入 API Key 以启动 Mingcrap。")
    st.stop()

client = OpenAI(api_key=api_key, base_url=base_url)

#人工确认

def manual_confirm(command):
    """Tkinter底层确认框"""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)  # 确保弹窗在最前面

    # 风险识别
    danger_keywords = ["rm", "del", "format", "shutdown", ">", "mv"]
    is_risky = any(kw in command.lower() for kw in danger_keywords)

    title = "⚠️ 危险操作确认" if is_risky else "操作授权请求"
    msg = f"Mingcrap 申请执行以下系统命令：\n\n> {command}\n\n是否允许？"

    res = messagebox.askyesno(title, msg)
    root.destroy()
    return res



#执行
def run_shell_command(command):
    if manual_confirm(command):
        try:
            # 超时处理
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=15)
            # gbk
            try:
                return f"【执行成功】:\n{result.decode('gbk')}"
            except:
                return f"【执行成功】:\n{result.decode('utf-8')}"
        except subprocess.CalledProcessError as e:
            # 报错详情
            err_msg = e.output.decode('gbk', errors='ignore')
            return f"【执行失败】: {err_msg}"
        except Exception as e:
            return f"【错误】: {str(e)}"
    else:
        return "【操作取消】: 用户拒绝了该命令。"




#Streamlit和决策循环

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
        "role": "system",
        "content": """你是一个名为 Mingcrap 的高级 AI 终端助手。你可以通过操作本地电脑(windows)来完成用户指令。

### 核心规则：
1. **思考与行动循环**：
   - 收到任务后，先进行分析（Thought），确定需要执行的操作。
   - 如果需要操作电脑，必须输出格式：`RUN_CMD: [具体的 Shell 命令]`。
   - 每次只执行**一个**命令，并等待系统反馈结果。
   - 根据系统返回的“观测结果”决定下一步：是继续尝试新命令，还是已经完成。

2. **自我修正**：
   - 如果命令报错，请分析报错原因（如路径空格、编码错误、权限不足），并在下一轮尝试不同的解决方案。
   - 不要重复尝试已经失败且未做修改的命令。

3. **任务终结**：
   - 当任务彻底完成时，必须以 `FINISH: [总结性描述]` 开头。

4. **安全警示**：
   - 在执行涉及删除、关机或大规模修改的命令前，请在 Thought 中提醒用户。

### 输出示例：
用户：帮我新建一个文件夹叫 test。
AI：我需要使用 mkdir 命令创建一个新文件夹。
RUN_CMD: mkdir test
"""
    }
]

# 显示历史对话
for msg in st.session_state.messages[1:]: 
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入
if prompt := st.chat_input("命令 Mingcrap 做点什么？", key="main_chat_input"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        thought_container = st.container()
        MAX_STEPS = 5
        for i in range(MAX_STEPS):
            with st.status(f"Mingcrap 正在进行第 {i + 1} 步决策...", expanded=True) as status:
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
                    cmd = full_response.split("RUN_CMD:")[1].strip().split('\n')[0]
                    st.write(f"🔍 识别到指令: `{cmd}`")
                    obs = run_shell_command(cmd)
                    st.code(obs, language="text")
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.session_state.messages.append({"role": "user", "content": f"SYSTEM_OBSERVATION: {obs}"})
                    status.update(label=f"✅ 步骤 {i + 1} 已完成", state="complete")
                else:
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    status.update(label="任务达成", state="complete", expanded=False)
                    break
        else:
            st.error("已达到最大限制，任务可能未完全完成。")

st.caption("Mingcrap 处于就绪状态")
