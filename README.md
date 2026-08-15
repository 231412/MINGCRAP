# MINGAGENT

Windows 本地终端 Agent，基于 Streamlit 和 OpenAI 兼容 API。

## 启动

```powershell
run.bat
```

或手动启动：

```powershell
python -m streamlit run app.py
```

或使用启动器（自动选择端口并打开浏览器）：

```powershell
python launcher.py [端口]
```

## 数据目录

所有可写数据（设置、密钥、经验、历史、审计、会话快照）默认放在项目目录；通过 PyInstaller 冻结运行时自动切换到 `%APPDATA%\MINGAGENT`。可用环境变量 `MINGAGENT_DATA_DIR` 显式指定位置。工具命令的工作目录在冻结运行时为 exe 所在目录，开发模式为项目根目录。

## 结构

- `app.py`：Streamlit 入口与轮询渲染
- `mingagent/`：核心逻辑
  - `llm.py`：提示词、上下文与响应解析（流式调用 + 指数退避重试）
  - `tools.py`：命令、Python 与联网搜索执行（可中断 + 编码回退链）
  - `runner.py`：后台线程中的 Agent 循环，与 UI 通过共享状态通信
  - `security.py`：统一风险拦截（Python 静态扫描 + 命令危险检测）、安全模式白名单与审计日志
  - `memory.py`：经验库（任务成功后提交，自动脱敏去重）
  - `history.py`：任务历史与整会话快照（`sessions/`）
  - `environment.py`：环境检测
  - `secrets.py`：API Key 本地持久化（明文，仅限个人机器）
  - `settings.py`：主题 / 强调色偏好（持久化到 `settings.json`）
  - `ui.py`：主题与界面组件
- `tests/`：pytest 测试套件（`python -m pytest tests`）
- `.streamlit/config.toml`：基础深色主题
- `legacy/`：旧版本归档

## 执行模型

Agent 循环运行在独立后台线程中：LLM 输出流式推送到界面，命令 / Python 由可取消的子进程执行（停止时以 `taskkill /T /F` 结束整个进程树），主线程每 0.4s 轮询刷新一次界面。LLM 调用失败自动指数退避重试；解析失败会回喂模型重新输出，连续 3 次才终止任务。

## 界面

- 暗色 / 亮色双主题 + 6 种强调色，侧边栏「外观」设置并持久化；
- 工具步骤以可折叠时间线展示（序号、状态色、耗时、复制按钮）；
- 运行中显示步骤进度条，快捷键 `Ctrl+Enter` 发送、`Esc` 停止；
- 任务结束弹出 toast；危险确认卡片内嵌最近审计记录。

## 安全

- 所有工具动作在执行前统一经过风险评估；`python` 动作同样受拦截（AST 静态扫描 + 正则兜底）。
- 侧边栏可开启「安全模式」：仅只读命令白名单自动执行，其余操作一律人工确认。
- 全部风险判定与执行结果追加记录于 `audit.jsonl`。
- 工具输出以 `<tool_output>` 包裹，并在系统提示词中声明为不可信数据，降低提示注入风险。
- 勾选「在本机记住 Key」会把 API Key 明文写入项目目录 `secrets.json`，仅限个人机器使用，请勿共享该目录。

## 记忆与历史

- 经验库仅在任务成功后提交，命令自动脱敏（绝对路径替换为 `<path>`）并按归一化形式去重，最多保留 20 条，可在侧边栏删除；
- 每次任务结束自动保存整会话快照（事件时间线 + 上下文消息，输出截断存储）到 `sessions/`，点击历史任务可查看并输入新指令继续对话。

## 测试

```powershell
pip install -r requirements-dev.txt
python -m pytest tests
```
