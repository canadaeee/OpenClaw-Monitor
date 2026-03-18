$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$backendVenvPython = Join-Path $projectRoot "backend\\.venv\\Scripts\\python.exe"

if (-not (Test-Path $backendVenvPython)) {
    throw "Missing backend virtual environment. Run: .\\scripts\\install-windows.ps1"
}

$ports = @(12888, 12889)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        throw "Port $port is already in use. Stop existing service with: .\\scripts\\stop-windows.ps1"
    }
}

Write-Host "Starting backend on 127.0.0.1:12888"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendDir'; & '$backendVenvPython' -m uvicorn app.main:app --host 127.0.0.1 --port 12888"

Write-Host "Starting frontend preview on 127.0.0.1:12889"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendDir'; npm run preview"

Write-Host ""
Write-Host "Dashboard: http://127.0.0.1:12889"
Write-Host "API:       http://127.0.0.1:12888/api/health"
