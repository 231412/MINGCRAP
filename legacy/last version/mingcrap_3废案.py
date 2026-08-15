import subprocess
import tkinter as tk
from tkinter import messagebox
import streamlit as st
from openai import OpenAI

# 初始化配置
st.set_page_config(page_title="Mingcrap Agent", page_icon="🦀")
st.title("🦀 MINGCRAP")

# 侧边栏配置
with st.sidebar:
    st.header("配置中心")
    api_key = st.text_input("输入 API Key", type="password")
    base_url = st.text_input("API 基地 URL", value="https://api.deepseek.com")
    model_name = st.text_input("模型名称", value="deepseek-chat")

    st.divider()
    max_steps = st.slider("最大决策步数", 1, 50, 10)

    if st.button("🧹 清空对话历史"):
        st.session_state.messages = [st.session_state.messages[0]]
        st.rerun()

if not api_key:
    st.warning("请先在侧边栏输入 API Key。")
    st.stop()

client = OpenAI(api_key=api_key, base_url=base_url)


# 授权逻辑
def manual_confirm(command):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    danger_keywords = ["rm", "del", "format", "shutdown", ">", "mv"]
    is_risky = any(kw in command.lower() for kw in danger_keywords)
    res = messagebox.askyesno("操作授权", f"申请执行命令：\n\n{command}")
    root.destroy()
    return res


# 执行逻辑
def run_shell_command(command):
    if manual_confirm(command):
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, timeout=20)
            try:
                return f"【执行成功】:\n{result.decode('gbk')}"
            except:
                return f"【执行成功】:\n{result.decode('utf-8', errors='ignore')}"
        except subprocess.CalledProcessError as e:
            err = e.output.decode('gbk', errors='ignore')
            return f"【执行失败】: {err}"
        except Exception as e:
            return f"【错误】: {str(e)}"
    return "【操作取消】: 用户拒绝。"


# 初始化
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": "你是一个名为 Mingcrap 的 Windows 终端大师。你的目标是逻辑严密地执行任务，避免无效循环。🛠 行为逻辑：1. **[span_1](start_span)环境先行**：在执行复杂任务（如 PDF 处理、图像转换）前，先通过 `pip list` 或 `where` 命令检查相关依赖。[span_1](end_span)2. **[span_2](start_span)单步执行**：严格遵守一次只输出一个 `RUN_CMD: [命令]`。[span_2](end_span)3. **[span_3](start_span)报错反思**：如果命令返回错误，严禁重复执行相同命令。你必须在 Thought 中分析原因（如：缺少库、路径空格、编码问题），并尝试更换方案（例如改用 Python 脚本执行）。[span_3](end_span)4. **[span_4](start_span)路径处理**：在 Windows 下处理文件路径时，务必使用引号包裹路径，防止空格导致失败。[span_4](end_span)### 🖼 特殊任务指引（如 PDF 转图片）：- 优先检查是否安装了 `PyMuPDF (fitz)` 或 `pdf2image`。- 如果缺失工具，请尝试 `pip install` 安装。- 如果多次命令行尝试失败，请编写一个临时 Python 脚本并运行它。### 📤 输出格式：- **Thought**: 简短分析现状及下一步计划。- **RUN_CMD**: [具体的 Shell 命令]- **[span_5](start_span)FINISH**: [任务完成后的总结描述][span_5](end_span)"
    }]

# 历史
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 主循环
if prompt := st.chat_input("输入任务..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        for i in range(max_steps):
            # 逻辑优化：上下文滑动窗口 (保留 System + 最近 8 条)
            context = st.session_state.messages
            if len(context) > 10:
                context = [context[0]] + context[-8:]

            with st.status(f"思考中 ({i + 1}/{max_steps})...") as status:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=context,
                    temperature=0.1,
                    stream=True
                )

                full_resp = ""
                placeholder = st.empty()
                for chunk in response:
                    content = chunk.choices[0].delta.content or ""
                    full_resp += content
                    placeholder.markdown(full_resp + "▌")
                placeholder.markdown(full_resp)

                if "RUN_CMD:" in full_resp:
                    cmd = full_resp.split("RUN_CMD:")[1].strip().split('\n')[0]
                    obs = run_shell_command(cmd)
                    st.code(obs)

                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                    st.session_state.messages.append({"role": "user", "content": f"SYSTEM_OBSERVATION: {obs}"})
                    status.update(label="步骤已响应", state="complete")
                else:
                    st.session_state.messages.append({"role": "assistant", "content": full_resp})
                    status.update(label="任务终结", state="complete")
                    break
        else:
            st.error("已达步数上限，请检查任务逻辑或清空历史。")
