@echo off
setlocal
cd /d "%~dp0"
set "NO_PAUSE="
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
if /I "%~1"=="--replace-only" (
    set "NO_PAUSE=1"
    goto replace_program_files
)

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
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --distpath build\packaged-dist --workpath build\pyinstaller MoneyPenny.spec
if errorlevel 1 goto build_failed

if not exist "build\packaged-dist\MoneyPenny\MoneyPenny.exe" goto build_failed

:replace_program_files
rem Keep mutable user data in dist\MoneyPenny intact. Replace only packaged
rem program files so rebuilding cannot erase settings, keys, logs, or history.
rem Stage the replacement beside the live files, then swap with rollback copies.
if not exist "dist\MoneyPenny" mkdir "dist\MoneyPenny"
if exist "dist\MoneyPenny\_internal.next" rmdir /s /q "dist\MoneyPenny\_internal.next"
if exist "dist\MoneyPenny\MoneyPenny.next.exe" del /q "dist\MoneyPenny\MoneyPenny.next.exe"
if exist "dist\MoneyPenny\_internal.previous" rmdir /s /q "dist\MoneyPenny\_internal.previous"
if exist "dist\MoneyPenny\MoneyPenny.previous.exe" del /q "dist\MoneyPenny\MoneyPenny.previous.exe"

xcopy "build\packaged-dist\MoneyPenny\_internal\*" "dist\MoneyPenny\_internal.next\" /e /i /y >nul
if errorlevel 1 goto build_failed
copy /y "build\packaged-dist\MoneyPenny\MoneyPenny.exe" "dist\MoneyPenny\MoneyPenny.next.exe" >nul
if errorlevel 1 goto build_failed
if not exist "dist\MoneyPenny\_internal.next" goto build_failed
if not exist "dist\MoneyPenny\MoneyPenny.next.exe" goto build_failed

if exist "dist\MoneyPenny\_internal" move /y "dist\MoneyPenny\_internal" "dist\MoneyPenny\_internal.previous" >nul
if errorlevel 1 goto replace_failed
if exist "dist\MoneyPenny\MoneyPenny.exe" move /y "dist\MoneyPenny\MoneyPenny.exe" "dist\MoneyPenny\MoneyPenny.previous.exe" >nul
if errorlevel 1 goto replace_failed
move /y "dist\MoneyPenny\_internal.next" "dist\MoneyPenny\_internal" >nul
if errorlevel 1 goto replace_failed
move /y "dist\MoneyPenny\MoneyPenny.next.exe" "dist\MoneyPenny\MoneyPenny.exe" >nul
if errorlevel 1 goto replace_failed
if not exist "dist\MoneyPenny\_internal" goto replace_failed
if not exist "dist\MoneyPenny\MoneyPenny.exe" goto replace_failed

if exist "dist\MoneyPenny\_internal.previous" rmdir /s /q "dist\MoneyPenny\_internal.previous"
if exist "dist\MoneyPenny\MoneyPenny.previous.exe" del /q "dist\MoneyPenny\MoneyPenny.previous.exe"

echo Built: %~dp0dist\MoneyPenny\MoneyPenny.exe
if not defined NO_PAUSE pause
exit /b 0

:replace_failed
echo Program-file replacement failed; restoring the previous runnable build...
if exist "dist\MoneyPenny\_internal" rmdir /s /q "dist\MoneyPenny\_internal"
if exist "dist\MoneyPenny\MoneyPenny.exe" del /q "dist\MoneyPenny\MoneyPenny.exe"
if exist "dist\MoneyPenny\_internal.previous" move /y "dist\MoneyPenny\_internal.previous" "dist\MoneyPenny\_internal" >nul
if exist "dist\MoneyPenny\MoneyPenny.previous.exe" move /y "dist\MoneyPenny\MoneyPenny.previous.exe" "dist\MoneyPenny\MoneyPenny.exe" >nul
if exist "dist\MoneyPenny\_internal.next" rmdir /s /q "dist\MoneyPenny\_internal.next"
if exist "dist\MoneyPenny\MoneyPenny.next.exe" del /q "dist\MoneyPenny\MoneyPenny.next.exe"
goto build_failed

:build_failed
echo.
echo MoneyPenny.exe was not built. Review the error above.
if not defined NO_PAUSE pause
exit /b 1
