$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"

Set-Location $backendDir
python -c "import sys; sys.path.insert(0, r'$backendDir'); from app.db import init_db; init_db(); print('SQLite initialized')"
