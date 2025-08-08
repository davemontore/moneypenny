# Voice Typing Launcher
Write-Host "Starting Voice Typing..." -ForegroundColor Green
Start-Process python -ArgumentList "voice_typing.py" -WindowStyle Hidden
Write-Host "Voice Typing is now running in the background!" -ForegroundColor Green
Write-Host "Look for the red microphone icon on your screen." -ForegroundColor Yellow
Start-Sleep -Seconds 3
