@echo off
REM Pulse Vector - Autonomous Daily AI Runner
REM Suitable for Windows Task Scheduler at 08:00 AM IST daily

cd /d "%~dp0\.."
echo [%DATE% %TIME%] Starting Pulse Vector Autonomous Daily Pipeline...
python scripts\run_autonomous_daemon.py --run-now
if %ERRORLEVEL% EQU 0 (
    echo [%DATE% %TIME%] Autonomous Daily Pipeline completed successfully.
) else (
    echo [%DATE% %TIME%] Autonomous Daily Pipeline failed with code %ERRORLEVEL%.
)
