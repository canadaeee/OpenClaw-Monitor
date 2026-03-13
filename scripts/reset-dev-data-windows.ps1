$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$dataDir = Join-Path $projectRoot "data"
$targets = @(
    (Join-Path $dataDir "monitor.db"),
    (Join-Path $dataDir "raw-events.jsonl"),
    (Join-Path $dataDir "node-events.jsonl")
)

foreach ($path in $targets) {
    if (Test-Path $path) {
        Remove-Item -Force $path
        Write-Host "Removed $path"
    }
    else {
        Write-Host "Skipped missing $path"
    }
}

Write-Host "Reinitializing SQLite database"
$backendDir = Join-Path $projectRoot "backend"
python -c "import sys; sys.path.insert(0, r'$backendDir'); from app.db import init_db; init_db(); print('database initialized')"

Write-Host "Development data reset complete."
