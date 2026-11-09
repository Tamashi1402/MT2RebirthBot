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

REM ------------------------------------------------------------------
REM Find a real, working Python - never just call "python" blindly.
REM On many PCs "python"/"python3" on PATH is only the Microsoft Store's
REM placeholder (App Execution Alias): running it prints a message like
REM "Python was not found; run without arguments to install" and exits,
REM even when a real Python is installed elsewhere or the PC was just
REM restarted. We prefer the "py" launcher (installed by python.org,
REM not the Store, so it isn't shadowed by that alias) and fall back
REM from there.
REM ------------------------------------------------------------------
setlocal enabledelayedexpansion
set "PY_EXE="
set "PY_ARGS="

REM 1) Prefer the "py" launcher.
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "1" >nul 2>nul
    if not errorlevel 1 (
        set "PY_EXE=py"
        set "PY_ARGS=-3"
    )
)

REM 2) Fall back to "python" on PATH, but skip any WindowsApps (Store) hit.
if not defined PY_EXE (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        if not defined PY_EXE (
            echo %%P | find /I "WindowsApps" >nul
            if errorlevel 1 (
                "%%P" -c "1" >nul 2>nul
                if not errorlevel 1 set "PY_EXE=%%P"
            )
        )
    )
)

REM 3) Fall back to "python3" on PATH.
if not defined PY_EXE (
    where python3 >nul 2>nul
    if not errorlevel 1 (
        python3 -c "1" >nul 2>nul
        if not errorlevel 1 set "PY_EXE=python3"
    )
)

REM 4) Last resort: look in the default per-user python.org install
REM    location even if it never made it onto PATH (newest version first).
if not defined PY_EXE (
    for /f "delims=" %%D in ('dir /b /ad /o-n "%LocalAppData%\Programs\Python\Python3*" 2^>nul') do (
        if not defined PY_EXE (
            if exist "%LocalAppData%\Programs\Python\%%D\python.exe" set "PY_EXE=%LocalAppData%\Programs\Python\%%D\python.exe"
        )
    )
)

if not defined PY_EXE (
    echo.
    echo ============================================================
    echo   Python was not found - or only the Microsoft Store's
    echo   placeholder is on PATH ^(that's the "not found; run
    echo   without arguments to install" message^).
    echo.
    echo   Fix:
    echo   1. Install Python from https://www.python.org/downloads/
    echo      - the official installer, NOT the Microsoft Store app.
    echo   2. On the first installer screen, tick
    echo      "Add python.exe to PATH" before clicking Install.
    echo   3. Restart this PC, then run START.bat again.
    echo.
    echo   If Python IS installed from python.org and this still
    echo   shows: open Windows Settings -^> Apps -^> Advanced app
    echo   settings -^> App execution aliases, and turn OFF
    echo   "python.exe" / "python3.exe" there.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

"%PY_EXE%" %PY_ARGS% code\bot.py %*
set "BOT_EXIT=%ERRORLEVEL%"

if not "%BOT_EXIT%"=="0" (
    echo.
    echo Bot exited with an error. Check logs\logs-YYYY-MM-DD.txt
    pause
)
