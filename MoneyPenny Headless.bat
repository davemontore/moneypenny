@echo off
setlocal
title MoneyPenny Voice Typing (Headless)
cd /d "%~dp0"

echo ====================================
echo    MoneyPenny Voice Typing v3.0
echo         Headless Mode
echo ====================================
echo.

echo Checking dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check >nul 2>&1

echo Starting application (headless - no GUI)...
echo - Hold RIGHT CTRL to dictate; release to transcribe
echo - Press ESC or Ctrl+Alt+Q to quit
echo.

python voice_to_text.py --headless

endlocal