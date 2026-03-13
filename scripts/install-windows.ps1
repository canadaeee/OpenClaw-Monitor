$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"

Write-Host "[1/5] Checking runtime requirements"
python --version | Out-Null
npm --version | Out-Null
python -m pip --version | Out-Null
if (-not (Test-Path (Join-Path $backendDir "requirements.txt"))) { throw "Missing backend/requirements.txt" }
if (-not (Test-Path (Join-Path $frontendDir "package.json"))) { throw "Missing frontend/package.json" }

Write-Host "[2/5] Installing backend dependencies"
Set-Location $backendDir
python -m pip install -r requirements.txt

Write-Host "[3/5] Initializing SQLite database"
python -c "import sys; sys.path.insert(0, r'$backendDir'); from app.db import init_db; init_db(); print('database initialized')"

Write-Host "[4/5] Installing frontend dependencies"
Set-Location $frontendDir
npm install

Write-Host "[5/5] Building frontend"
npm run build

Write-Host ""
Write-Host "OpenClaw Monitor install complete."
Write-Host "Start with: .\scripts\start-windows.ps1"
