$Action = New-ScheduledTaskAction -Execute "c:\Users\addyt\OneDrive\Desktop\pulse-vector\run_daily.bat"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8am
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun

Register-ScheduledTask -TaskName "PulseVectorDaily" -Action $Action -Trigger $Trigger -Settings $Settings -Force

Write-Host "Success! Pulse Vector will now run every day at 8:00 AM."
Write-Host "If your laptop is off at 8:00 AM, it will run automatically the moment you turn it on."
