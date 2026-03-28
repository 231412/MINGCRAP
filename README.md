1. 核心架构：基于 LLM 的闭环控制系统
Mingcrap 是一个集成了大语言模型（LLM）推理能力与本地系统交互接口的自主 Agent 框架。它通过以下循环实现任务目标：
 * 感知（Perception）：通过 Streamlit UI 接收用户非结构化的自然语言指令。
 * 规划（Planning）：利用模型生成思维链，将复杂目标拆解为可执行的 Shell 指令（RUN_CMD 协议）。
 * 执行（Execution）：通过 Python subprocess 模块在宿主机环境调用系统级工具。
 * 反馈（Feedback）：捕获标准输出（stdout）及错误流（stderr），并将其作为上下文回传给 LLM 进行结果评估与错误修正。
2. 安全工程：多模态拦截机制
针对 AI 代理可能带来的系统风险，本项目设计了两层安全防护：
 * 启发式扫描：在执行层预设 danger_keywords 列表（如 rm, del, shutdown 等），自动识别高危指令。
 * 人机回路（Human-in-the-Loop）校验：利用 Tkinter 构建模态对话框，强制将控制权交还给物理用户，未经授权严禁执行任何写操作。
 3.运用了Windows的.bat代码作为启动器，具体请见部署教程.txt
 4. 开发者总结
> “Mingcrap 不仅仅是一个聊天机器人，它是一个具备环境感知能力和自我修正逻辑的终端操作代理。它证明了通过合理的 Prompt Engineering 与安全拦截设计，LLM 可以安全地作为生产力工具直接参与底层系统管理。”
