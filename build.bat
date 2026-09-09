@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo  Password Vault Pro — сборка Windows exe
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [Ошибка] Python не найден.
    echo Установите Python 3.11+ с https://www.python.org/downloads/
    echo При установке отметьте "Add python.exe to PATH".
    pause
    exit /b 1
)

echo [1/4] Создание виртуального окружения...
if not exist ".venv-build\Scripts\python.exe" (
    python -m venv .venv-build
    if errorlevel 1 (
        echo [Ошибка] Не удалось создать venv.
        pause
        exit /b 1
    )
)

call ".venv-build\Scripts\activate.bat"

echo [2/4] Установка зависимостей...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
    echo [Ошибка] pip install не удался.
    pause
    exit /b 1
)

echo [3/4] Сборка exe через PyInstaller...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --noconfirm --clean PasswordVaultPro.spec
if errorlevel 1 (
    echo [Ошибка] PyInstaller не смог собрать exe.
    pause
    exit /b 1
)

echo [4/4] Готово.
echo.
echo Файл: dist\PasswordVaultPro.exe
echo Рядом с exe появятся папки database\ и backups\ при первом запуске.
echo.

if exist "dist\PasswordVaultPro.exe" (
    explorer dist
) else (
    echo [Ошибка] dist\PasswordVaultPro.exe не найден.
    pause
    exit /b 1
)

pause
