@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-MoneyPennyShortcuts.ps1" -RestartExplorer
if errorlevel 1 (
    echo.
    echo MoneyPenny's shortcuts could not be installed.
    pause
    exit /b 1
)

echo.
echo MoneyPenny is installed in the Start Menu and pinned to the taskbar.
pause
