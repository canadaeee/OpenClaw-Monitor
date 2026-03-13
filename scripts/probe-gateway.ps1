$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"

Set-Location $backendDir
python -c "import sys; sys.path.insert(0, r'$backendDir'); from app.collector import OpenClawCollector; from app.settings import load_gateway_settings; print(OpenClawCollector(load_gateway_settings()).probe_http())"
