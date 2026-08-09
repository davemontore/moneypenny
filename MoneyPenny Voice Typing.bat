@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    call "Install MoneyPenny.bat" --no-pause
    if errorlevel 1 exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "%~dp0voice_to_text.py"
exit /b 0