@echo off
setlocal
title MoneyPenny Voice Typing
cd /d "%~dp0"

echo ====================================
echo    MoneyPenny Voice Typing v2.2
echo ====================================
echo.

echo Checking dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check >nul 2>&1

echo Starting application (hold RIGHT CTRL to dictate; Ctrl+Alt+Q to quit)...
echo.

python voice_to_text.py

endlocal
