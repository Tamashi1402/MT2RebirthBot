# MT2 Rebirth Bot - Build
$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot
if (-not (Test-Path (Join-Path $ProjectRoot "code\bot.py"))) {
    Fail "code\bot.py not found in $ProjectRoot. Run BUILD from the unzipped bot folder."
}

function Fail($msg) {
    Write-Host " [ERROR] $msg" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host " ========================================================" -ForegroundColor Cyan
Write-Host "  MT2 Rebirth Bot - Build" -ForegroundColor Cyan
Write-Host " ========================================================" -ForegroundColor Cyan
Write-Host ""

try { $pyver = python --version 2>&1 } catch { Fail "Python 3.10+ was not found in PATH." }
Write-Host " [OK] $pyver" -ForegroundColor Green

Write-Host " [*] Creating clean virtual environment..."
if (Test-Path build_venv) { Remove-Item build_venv -Recurse -Force }
python -m venv build_venv
if ($LASTEXITCODE -ne 0) { Fail "Failed to create build virtual environment." }
& build_venv\Scripts\python -m pip install --upgrade pip *>$null
& build_venv\Scripts\python -m pip install pyinstaller pillow -r requirements.txt
if ($LASTEXITCODE -ne 0) { Fail "Failed to install requirements." }
Write-Host " [OK] Build environment ready." -ForegroundColor Green
if (-not (Test-Path "tesseract-ocr\tesseract.exe")) { Fail "tesseract-ocr\tesseract.exe not found. OCR cannot be packed into the exe." }
Write-Host " [OK] Bundled tesseract-ocr\ will be packed inside the exe." -ForegroundColor Green

$iconArg = @()
if (-not (Test-Path icon.ico) -and (Test-Path icon.png)) {
    Write-Host " [*] Converting icon.png to icon.ico..."
    & build_venv\Scripts\python -c "from PIL import Image; Image.open('icon.png').save('icon.ico', format='ICO', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
}
if (Test-Path icon.ico) {
    $iconArg = @("--icon", "icon.ico")
    Write-Host " [OK] Using icon.ico" -ForegroundColor Green
} else {
    Write-Host " [WARN] No icon.ico / icon.png - exe will use the default icon." -ForegroundColor Yellow
}

Write-Host " [*] Cleaning previous output..."
@("build", "dist", "output") | ForEach-Object { if (Test-Path $_) { Remove-Item $_ -Recurse -Force } }
Get-ChildItem -Filter "*.spec" -ErrorAction SilentlyContinue | Remove-Item -Force
New-Item -ItemType Directory output | Out-Null
New-Item -ItemType Directory output\data | Out-Null

Write-Host " [*] Building MT2RebirthBot.exe..." -ForegroundColor Cyan
$botArgs = @(
    "--onefile", "--noconsole", "--noconfirm",
    "--name", "MT2RebirthBot"
) + $iconArg + @(
    "--distpath", "output",
    "--workpath", "build",
    "--specpath", ".",
    "--manifest", "mt2.manifest",
    "--paths", "code",
    "--add-data", "icon.png;.",
    "--add-data", "icon.ico;.",
    "--add-data", "data\config.json;data",
    "--add-data", "code\blockly;blockly",
    "--add-data", "code\macro_engine;macro_engine",
    "--add-data", "tesseract-ocr;tesseract-ocr",
    "--hidden-import=flask",
    "--hidden-import=keyboard",
    "--hidden-import=mouse",
    "--hidden-import=PIL",
    "--hidden-import=PIL._imaging",
    "--hidden-import=PIL.Image",
    "--hidden-import=PIL.ImageGrab",
    "--hidden-import=cv2",
    "--hidden-import=numpy",
    "--hidden-import=pytesseract",
    "--hidden-import=werkzeug",
    "--hidden-import=jinja2",
    "--collect-all=mss",
    "--collect-all=webview",
    "--hidden-import=webview",
    "--hidden-import=webview.platforms.winforms",
    "--hidden-import=psutil",
    "--hidden-import=macro_logic",
    "--hidden-import=macro_runner",
    "--hidden-import=manual_strength",
    "--hidden-import=teleport_menu",
    "--hidden-import=run_recorder",
    "--hidden-import=version",
    "--hidden-import=mode_runner",
    "--hidden-import=lobby",
    "--hidden-import=net_guard",


    "--hidden-import=macro_engine",
    "--hidden-import=macro_engine.app",
    "--hidden-import=macro_engine.macro_engine",
    "--hidden-import=macro_engine.overlay",
    "--hidden-import=macro_engine.macro_logic",
    "--hidden-import=crater",
    "--hidden-import=crater.loop",
    "--hidden-import=crater.overlay",
    "--hidden-import=crater.detector",
    "--hidden-import=crater.input",
    "--hidden-import=crater.timer_tracker",
    "--hidden-import=zytos",
    "--hidden-import=zytos.loop",
    "--hidden-import=zytos.dodge",
    "--hidden-import=zytos.input",
    "--hidden-import=zytos.detector",
    "--exclude-module=ultralytics",
    "--exclude-module=torch",
    "--exclude-module=torchvision",
    (Join-Path $ProjectRoot "code\bot.py")
)
& build_venv\Scripts\python -m PyInstaller @botArgs
if ($LASTEXITCODE -ne 0) { Fail "MT2RebirthBot.exe build failed." }
if (-not (Test-Path "output\MT2RebirthBot.exe")) { Fail "output\MT2RebirthBot.exe was not created." }
Write-Host " [OK] MT2RebirthBot.exe built." -ForegroundColor Green

Write-Host " [*] Copying macros + config + bundled Tesseract..."
if (-not (Test-Path "macros")) { Fail "macros folder not found." }
Copy-Item "macros" "output\macros" -Recurse -Force
if (-not (Test-Path "data\config.json")) { Fail "data\config.json not found." }
New-Item -ItemType Directory -Force -Path "output\data" | Out-Null
Copy-Item "data\config.json" "output\data\config.json" -Force
if (Test-Path "data\default_regions.json") {
    Copy-Item "data\default_regions.json" "output\data\default_regions.json" -Force
}
if (Test-Path "data\first_steps") {
    Copy-Item "data\first_steps" "output\data\first_steps" -Recurse -Force
}
if (Test-Path "tesseract-ocr") {
    Copy-Item "tesseract-ocr" "output\tesseract-ocr" -Recurse -Force
    Write-Host " [OK] Bundled tesseract-ocr/" -ForegroundColor Green
} else {
    Write-Host " [WARN] tesseract-ocr/ missing - OCR will need a system Tesseract install." -ForegroundColor Yellow
}
Write-Host " [OK] Assets copied." -ForegroundColor Green

Write-Host " [*] Cleaning temp files..."
@("build", "build_venv") | ForEach-Object { if (Test-Path $_) { Remove-Item $_ -Recurse -Force } }
Get-ChildItem -Filter "*.spec" -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Host ""
Write-Host " ========================================================" -ForegroundColor Cyan
Write-Host "  BUILD COMPLETE" -ForegroundColor Green
Write-Host ""
Write-Host "   Tesseract OCR is packed inside the exe (users need only the .exe + macros/data)."
Write-Host "  output\macros\"
Write-Host "  output\data\config.json"
Write-Host "  output\data\first_steps\"
Write-Host "  output\tesseract-ocr\"
Write-Host ""
Write-Host "  Distribute the whole output\ folder."
Write-Host " ========================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
exit 0
