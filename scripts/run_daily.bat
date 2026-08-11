@echo off
set PATH=%PATH%;C:\Program Files\Git\cmd
cd /d "%~dp0.."
if not exist logs mkdir logs
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd'"') do set LOG_DATE=%%i
echo [%date% %time%] Starting Daily Run >> logs\pipeline_%LOG_DATE%.log
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" src\pipeline.py --all
) else (
    python src\pipeline.py --all
)
