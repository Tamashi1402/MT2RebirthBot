@echo off
set "ROOT=%~dp0.."
cd /d "%ROOT%"
echo ============================================
echo   MT2 Bot - Installing requirements
echo ============================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Make sure Python is installed and added to PATH.
    pause
    exit /b 1
)

echo Installing Python packages...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Something went wrong during installation.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Done! You can now run START.bat
echo ============================================
if not defined NO_PAUSE pause
