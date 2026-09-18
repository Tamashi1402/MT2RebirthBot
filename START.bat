@echo off
title MT2 Rebirth Bot
cls

cd /d "%~dp0"

REM If someone extracted/ran this from logs\, jump to the real bot folder.
for %%I in ("%~dp0.") do set "HERE=%%~nxI"
if /I "%HERE%"=="logs" (
    if exist "%~dp0..\code\bot.py" (
        cd /d "%~dp0.."
    )
)

if not exist "code\bot.py" (
    echo.
    echo Run START.bat from the bot folder the one with code\ and data\
    echo Not from logs\
    echo.
    pause
    exit /b 1
)
if not exist "data\config.json" (
    echo.
    echo data\config.json is missing.
    echo Extract the zip into the bot folder next to START.bat, not into logs\
    echo.
    pause
    exit /b 1
)

REM Bundled Tesseract — so pytesseract finds it even before Python runs.
if exist "%cd%\tesseract-ocr\tesseract.exe" (
    set "PATH=%cd%\tesseract-ocr;%PATH%"
    set "TESSDATA_PREFIX=%cd%\tesseract-ocr\tessdata"
)
python code\bot.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Bot exited with an error. Check logs\logs-YYYY-MM-DD.txt
    pause
)
