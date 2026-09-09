@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set PY=
where python >nul 2>&1
if not errorlevel 1 set PY=python
if not defined PY (
    where py >nul 2>&1
    if not errorlevel 1 set PY=py -3
)
if not defined PY (
    echo [ERROR] Python not found.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo Enable "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

echo Building Password Vault Pro...
%PY% build.py
set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
    echo.
    echo [ERROR] Build failed with code %ERR%.
)
echo.
pause
exit /b %ERR%
