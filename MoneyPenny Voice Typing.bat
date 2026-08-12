@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    call "Install MoneyPenny.bat" --no-pause
    if errorlevel 1 exit /b 1
)

set "MONEYPENNY_SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\MoneyPenny.lnk"
if exist "%MONEYPENNY_SHORTCUT%" (
    start "" "%MONEYPENNY_SHORTCUT%"
) else if exist "dist\MoneyPenny\MoneyPenny.exe" (
    start "" "dist\MoneyPenny\MoneyPenny.exe" --app-dir "%~dp0"
) else (
    start "" ".venv\Scripts\pythonw.exe" "%~dp0voice_to_text.py"
)
exit /b 0
