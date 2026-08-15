@echo off
title MINGAGENT Builder
cd /d "%~dp0"

set "PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
if not exist "%PY%" set "PY=python"

echo [1/3] Installing build dependencies...
"%PY%" -m pip install -r requirements.txt --quiet
"%PY%" -m pip install pyinstaller --quiet

echo [2/3] Building...
"%PY%" -m PyInstaller MINGAGENT.spec --noconfirm --clean

echo.
echo [3/3] Done. Artifact: dist\MINGAGENT.exe
pause
