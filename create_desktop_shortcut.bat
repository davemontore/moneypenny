@echo off
title Create Desktop Shortcut
echo Creating desktop shortcut for Voice Typing...
echo.

REM Get the current directory (where the voice_typing.py file is located)
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

REM Get the desktop path
for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop 2^>nul') do set "DESKTOP=%%b"

REM Create the shortcut
echo Creating shortcut on desktop...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\Voice Typing.lnk'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = '\"%CURRENT_DIR%\voice_typing.py\"'; $Shortcut.WorkingDirectory = '%CURRENT_DIR%'; $Shortcut.Description = 'Voice Typing Application'; $Shortcut.IconLocation = '%CURRENT_DIR%\voice_typing.py,0'; $Shortcut.Save()"

if errorlevel 1 (
    echo ERROR: Failed to create desktop shortcut
    echo You can still run the app by double-clicking run_voice_typing.bat
    pause
    exit /b 1
)

echo.
echo SUCCESS: Desktop shortcut created!
echo You can now double-click "Voice Typing" on your desktop to run the app.
echo.
pause
