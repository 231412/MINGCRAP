@echo off
title Mingcrap Launcher

:: 初始颜色
color 9
chcp 65001 >nul

echo ==========================================
echo             Mingcrap Agent
echo ==========================================
echo.

:: 检查 Python
color 8
echo [1/2] 正在检查环境依赖...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 4
    echo [错误] 未检测到 Python，请安装 Python 并添加到环境变量
    pause
    exit /b 1
)

:: 安装依赖
color 9
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    color 3
    echo 正在安装依赖...
    python -m pip install streamlit openai --quiet
)

:: 成功提示
color 2
echo [完成] 依赖检查完成
echo.

:: 启动
color 9
echo [2/2] 正在启动 UI 界面...
echo.
echo 启动成功后，请在浏览器中访问显示的地址
echo 提示: 按 Ctrl+C 可停止服务
echo.

cd /d "%~dp0"
python -m streamlit run mingcrap.py

pause