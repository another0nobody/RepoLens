@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    echo 使用虚拟环境 ..\.venv
    "..\.venv\Scripts\python.exe" run.py --open
) else (
    echo 使用系统 Python
    python run.py --open
)

if errorlevel 1 pause
