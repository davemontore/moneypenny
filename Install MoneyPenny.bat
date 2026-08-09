@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo       MoneyPenny Setup
echo ========================================
echo.

rem Prefer a tested Python version when several are installed.
for %%V in (3.13 3.12 3.11 3.10) do (
    py -%%V -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -%%V"
        goto python_found
    )
)

python -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info < (3, 14) else 1)" >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    goto python_found
)

echo MoneyPenny needs Python 3.10, 3.11, 3.12, or 3.13.
echo Download Python from: https://www.python.org/downloads/windows/
echo During installation, check "Add Python to PATH".
goto setup_failed

:python_found
echo Using:
%PYTHON_CMD% --version
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating MoneyPenny's private Python environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto setup_failed
)

echo Installing the tested MoneyPenny components...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto setup_failed

if not exist "lexicon.txt" copy /Y "lexicon.example.txt" "lexicon.txt" >nul

echo Checking the installation...
".venv\Scripts\python.exe" -c "import customtkinter, faster_whisper, keyboard, PIL, pyaudio, pynput, pystray, requests"
if errorlevel 1 goto setup_failed
".venv\Scripts\python.exe" -m py_compile voice_to_text.py gui.py
if errorlevel 1 goto setup_failed

echo.
echo Setup complete. Double-click "MoneyPenny Voice Typing.bat" to start.
if /I not "%~1"=="--no-pause" pause
exit /b 0

:setup_failed
echo.
echo Setup did not finish. The message above explains what went wrong.
echo Nothing outside the MoneyPenny folder was changed.
pause
exit /b 1