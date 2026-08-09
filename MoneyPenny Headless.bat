@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call "Install MoneyPenny.bat" --no-pause
    if errorlevel 1 exit /b 1
)

echo Starting MoneyPenny without the settings window or tray icon...
echo Hold RIGHT CTRL to record, release to transcribe.
echo Press ESC or Ctrl+Alt+Q to quit.
echo.
".venv\Scripts\python.exe" voice_to_text.py --headless
if errorlevel 1 pause