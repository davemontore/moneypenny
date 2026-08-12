@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo MoneyPenny must be installed before building the executable.
    echo Run "Install MoneyPenny.bat" first.
    goto build_failed
)

echo Installing MoneyPenny's Windows build tool...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-build.txt
if errorlevel 1 (
    echo The default package server failed; trying MoneyPenny's fallback mirror...
    ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r requirements-build.txt
    if errorlevel 1 goto build_failed
)

echo Building the branded MoneyPenny.exe...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath dist --workpath build\pyinstaller MoneyPenny.spec
if errorlevel 1 goto build_failed

if not exist "dist\MoneyPenny\MoneyPenny.exe" goto build_failed

echo Built: %~dp0dist\MoneyPenny\MoneyPenny.exe
if /I not "%~1"=="--no-pause" pause
exit /b 0

:build_failed
echo.
echo MoneyPenny.exe was not built. Review the error above.
if /I not "%~1"=="--no-pause" pause
exit /b 1
