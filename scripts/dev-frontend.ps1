$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $projectRoot "frontend"

Set-Location $frontendDir
npm run dev -- --host 127.0.0.1 --port 12889
