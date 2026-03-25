import os
import subprocess
import streamlit as st
from openai import OpenAI
import tkinter as tk
from tkinter import messagebox

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
        {"role": "system",
         "content": "你是一个名为 Mingcrap 的 AI。你可以通过回复 'RUN_CMD: [命令]' 来操作电脑。任务完成后回复 'FINISH: [总结]'。"}
    ]

# 显示历史对话
for msg in st.session_state.messages[1:]:  # 跳过提示词
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 输入
if prompt := st.chat_input("命令 Mingcrap 做点什么？"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 思考循环
    with st.chat_message("assistant"):
        # 状态容器
        with st.status("Mingcrap 正在思考...", expanded=True) as status:
            for _ in range(3):#在这里更改循环次数，3次节省钱包这一块
                response = client.chat.completions.create(
                    model=model_name,
                    messages=st.session_state.messages,
                    temperature=0.1
                )
                ai_content = response.choices[0].message.content

                if "RUN_CMD:" in ai_content:
                    cmd = ai_content.split("RUN_CMD:")[1].strip()
                    st.write(f"👉 尝试执行命令: `{cmd}`")

                    # 执行工具
                    obs = run_shell_command(cmd)

                    # 实时展示执行结果
                    st.code(obs, language="text")

                    # 更新上下文
                    st.session_state.messages.append({"role": "assistant", "content": ai_content})
                    st.session_state.messages.append({"role": "user", "content": f"系统观测结果: {obs}"})
                    continue
                else:
                    # 最终完成
                    status.update(label="任务完成！", state="complete", expanded=False)
                    st.markdown(ai_content)
                    st.session_state.messages.append({"role": "assistant", "content": ai_content})
                    break

st.success("Mingcrap 运行中 - 准备就绪")
