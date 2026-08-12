@echo off
setlocal
cd /d "%~dp0"

call "%~dp0Build MoneyPenny.exe.bat" --no-pause
if errorlevel 1 (
    echo.
    echo MoneyPenny.exe could not be built.
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-MoneyPennyShortcuts.ps1" -RestartExplorer
if errorlevel 1 (
    echo.
    echo MoneyPenny's taskbar shortcut could not be installed.
    pause
    exit /b 1
)

echo.
echo MoneyPenny's taskbar identity and icon have been refreshed.
pause
