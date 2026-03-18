$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$venvDir = Join-Path $backendDir ".venv"
$venvPython = Join-Path $venvDir "Scripts\\python.exe"

Write-Host "[1/5] Checking runtime requirements"
python --version | Out-Null
npm --version | Out-Null
python -m pip --version | Out-Null
if (-not (Test-Path (Join-Path $backendDir "requirements.txt"))) { throw "Missing backend/requirements.txt" }
if (-not (Test-Path (Join-Path $frontendDir "package.json"))) { throw "Missing frontend/package.json" }

Write-Host "[2/6] Creating backend virtual environment"
if (-not (Test-Path $venvPython)) {
    Set-Location $backendDir
    python -m venv $venvDir
}

Write-Host "[3/6] Installing backend dependencies"
Set-Location $backendDir
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host "[4/6] Initializing SQLite database"
& $venvPython -c "import sys; sys.path.insert(0, r'$backendDir'); from app.db import init_db; init_db(); print('database initialized')"

Write-Host "[5/6] Installing frontend dependencies"
Set-Location $frontendDir
if (Test-Path (Join-Path $frontendDir "package-lock.json")) {
    npm ci
} else {
    npm install
}

Write-Host "[6/6] Building frontend"
npm run build

Write-Host ""
Write-Host "OpenClaw Monitor install complete."
Write-Host "Backend virtual environment: $venvDir"
Write-Host "Start with: .\scripts\run-windows.ps1"
