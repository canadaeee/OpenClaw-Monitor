$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendVenvPython = Join-Path $projectRoot "backend\\.venv\\Scripts\\python.exe"

if (-not (Test-Path $backendVenvPython)) {
    Write-Host "Backend venv not found. Running installer..."
    & (Join-Path $PSScriptRoot "install-windows.ps1")
}

& (Join-Path $PSScriptRoot "start-windows.ps1")

