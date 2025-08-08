@echo off
title MoneyPenny Voice Typing
cd /d "%~dp0"

echo ====================================
echo    MoneyPenny Voice Typing v2.0
echo ====================================
echo.

echo Checking dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check >nul 2>&1

echo Starting application...
echo.

python voice_to_text.py

if errorlevel 1 (
    echo.
    echo ====================================
    echo ERROR: Failed to start the application
    echo ====================================
    echo.
    echo Trying to install dependencies explicitly...
    pip install -r requirements.txt
    echo.
    echo Please try running the application again.
    pause
)
