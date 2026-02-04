@echo off
cd /d "c:\Users\addyt\OneDrive\Desktop\pulse-vector"
python auto_pulse.py
python process_data.py

:: --- 1. Git Automation (Push to GitHub) ---
echo Pushing changes to GitHub...
git add pulse_archive
git commit -m "Auto-generated content update"
git push

:: Backing up to Google Drive
xcopy "pulse_archive" "G:\PulseVectorBackups\pulse_archive" /E /I /Y /D
echo Backup to Google Drive Complete!

