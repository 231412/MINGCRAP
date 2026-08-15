@echo off
title MINGAGENT Launcher
color 9

echo ==========================================
echo             MINGAGENT Agent
echo ==========================================
echo.

echo [1/2] Checking Python...

set "PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" --version >nul 2>&1
if errorlevel 1 (
    color 4
    echo [ERROR] Python not found
    pause
    exit /b 1
)

echo    Python: %PY%

"%PY%" -c "import streamlit, openai, requests" >nul 2>&1
if errorlevel 1 (
    color 3
    echo [Installing] Installing dependencies...
    "%PY%" -m pip install streamlit openai requests --quiet
)

color 2
echo [OK] Environment ready
echo.

cd /d "%~dp0"

if not exist expertise.json echo [] > expertise.json

echo [2/2] Launching...
echo.
"%PY%" -m streamlit run app.py --server.headless true

pause
