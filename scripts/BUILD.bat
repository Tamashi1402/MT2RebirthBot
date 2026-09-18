@echo off
setlocal EnableExtensions EnableDelayedExpansion
for %%I in ("%~dp0..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
title MT2 Rebirth Bot - Build

echo.
echo  ========================================================
echo   MT2 Rebirth Bot - Build
echo  ========================================================
echo.
echo  [OK] Project root: %CD%

if not exist "%ROOT%\code\bot.py" (
    echo  [ERROR] code\bot.py not found in %CD%
    echo          Run BUILD.bat from the unzipped bot folder, not from output\ or scripts\.
    goto :fail
)

python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python 3.10+ was not found in PATH.
    goto :fail
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  [OK] %%v

echo  [*] Creating clean virtual environment...
if exist build_venv rmdir /s /q build_venv >nul 2>&1
python -m venv build_venv
if errorlevel 1 (
    echo  [ERROR] Failed to create build virtual environment.
    goto :fail
)
build_venv\Scripts\python -m pip install --upgrade pip >nul
build_venv\Scripts\python -m pip install pyinstaller pillow -r requirements.txt
if errorlevel 1 (
    echo  [ERROR] Failed to install requirements.
    goto :fail
)
echo  [OK] Build environment ready.

if not exist "tesseract-ocr\tesseract.exe" (
    echo  [ERROR] tesseract-ocr\tesseract.exe not found. OCR cannot be packed into the exe.
    goto :fail
)
echo  [OK] Bundled tesseract-ocr\ will be packed inside the exe.


set "ICON_ARGS="
if not exist icon.ico (
    if exist icon.png (
        echo  [*] Converting icon.png to icon.ico...
        build_venv\Scripts\python -c "from PIL import Image; Image.open('icon.png').save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
    )
)
if exist icon.ico (
    set "ICON_ARGS=--icon icon.ico"
    echo  [OK] Using icon.ico
) else (
    echo  [WARN] No icon.ico / icon.png - exe will use the default icon.
)

echo  [*] Cleaning previous output...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist output rmdir /s /q output >nul 2>&1
del /q *.spec >nul 2>&1
mkdir output
mkdir output\data

echo  [*] Building MT2RebirthBot.exe...
build_venv\Scripts\python -m PyInstaller ^
    --onefile --noconsole --noconfirm ^
    --name MT2RebirthBot ^
    %ICON_ARGS% ^
    --distpath output --workpath build --specpath . ^
    --manifest mt2.manifest ^
    --paths code ^
    --add-data "icon.png;." ^
    --add-data "icon.ico;." ^
    --add-data "data\config.json;data" ^
    --add-data "code\blockly;blockly" ^
    --add-data "code\macro_engine;macro_engine" ^
    --add-data "tesseract-ocr;tesseract-ocr" ^
    --hidden-import=flask ^
    --hidden-import=keyboard ^
    --hidden-import=mouse ^
    --hidden-import=PIL --hidden-import=PIL._imaging --hidden-import=PIL.Image --hidden-import=PIL.ImageGrab ^
    --hidden-import=cv2 --hidden-import=numpy --hidden-import=pytesseract ^
    --hidden-import=werkzeug --hidden-import=jinja2 ^
    --collect-all=mss --collect-all=webview ^
    --hidden-import=webview --hidden-import=webview.platforms.winforms ^
    --hidden-import=psutil ^
    --hidden-import=macro_logic --hidden-import=macro_runner --hidden-import=manual_strength ^
    --hidden-import=teleport_menu --hidden-import=run_recorder --hidden-import=version --hidden-import=mode_runner ^
    --hidden-import=lobby --hidden-import=net_guard ^
    --hidden-import=macro_engine --hidden-import=macro_engine.app --hidden-import=macro_engine.macro_engine ^
    --hidden-import=macro_engine.overlay --hidden-import=macro_engine.macro_logic ^
    --hidden-import=crater --hidden-import=crater.loop --hidden-import=crater.overlay --hidden-import=crater.detector --hidden-import=crater.input --hidden-import=crater.timer_tracker ^
    --hidden-import=zytos --hidden-import=zytos.loop --hidden-import=zytos.dodge --hidden-import=zytos.input --hidden-import=zytos.detector ^
    --exclude-module=ultralytics --exclude-module=torch --exclude-module=torchvision ^
    "%ROOT%\code\bot.py"
if errorlevel 1 (
    echo  [ERROR] MT2RebirthBot.exe build failed.
    goto :fail
)
if not exist "output\MT2RebirthBot.exe" (
    echo  [ERROR] output\MT2RebirthBot.exe was not created.
    goto :fail
)
echo  [OK] MT2RebirthBot.exe built.

echo  [*] Copying macros + config...
if not exist "macros\" (
    echo  [ERROR] macros folder not found.
    goto :fail
)
build_venv\Scripts\python -c "import os,shutil; shutil.copytree('macros','output/macros', dirs_exist_ok=True)"
if not exist "data\config.json" (
    echo  [ERROR] data\config.json not found.
    goto :fail
)
copy /y "data\config.json" "output\data\config.json" >nul
if exist "data\default_regions.json" copy /y "data\default_regions.json" "output\data\default_regions.json" >nul
if exist "data\first_steps\" build_venv\Scripts\python -c "import shutil; shutil.copytree('data/first_steps','output/data/first_steps', dirs_exist_ok=True)"
if not exist "output\data\config.json" (
    echo  [ERROR] Failed to copy config.json.
    goto :fail
)
if exist "tesseract-ocr\tesseract.exe" (
    echo  [*] Copying bundled tesseract-ocr...
    build_venv\Scripts\python -c "import shutil; shutil.copytree('tesseract-ocr','output/tesseract-ocr', dirs_exist_ok=True)"
    echo  [OK] Bundled tesseract-ocr/
) else (
    echo  [WARN] tesseract-ocr missing - OCR will need a system Tesseract install.
)
echo  [OK] Assets copied.

echo  [*] Cleaning temp files...
if exist build rmdir /s /q build >nul 2>&1
if exist build_venv rmdir /s /q build_venv >nul 2>&1
del /q *.spec >nul 2>&1

echo.
echo  ========================================================
echo   BUILD COMPLETE
echo  ========================================================
echo.
echo   output\MT2RebirthBot.exe   (Tesseract OCR is packed INSIDE this file)
echo   output\macros\
echo   output\data\config.json
echo   output\data\first_steps\
echo   output\tesseract-ocr\      (fallback copy next to the exe)
echo.
echo   Users who only get the .exe still have OCR.
echo   Re-run this BUILD.start / BUILD.bat after pulling 1.7.2.
echo.
pause
exit /b 0

:fail
echo.
echo  Build stopped. Fix the error and run BUILD.bat again.
echo.
pause
exit /b 1
