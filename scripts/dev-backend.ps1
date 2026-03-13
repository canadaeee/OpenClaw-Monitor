$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"

Set-Location $backendDir
python -m uvicorn app.main:app --host 127.0.0.1 --port 12888 --reload
