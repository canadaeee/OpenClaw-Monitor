$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$branch = "main"

if (-not ([string]::IsNullOrWhiteSpace((git -C $projectRoot status --porcelain)))) {
    throw "Working tree is not clean. Please commit/stash your changes before update."
}

Write-Host "[1/3] Updating repository"
git -C $projectRoot fetch origin $branch
git -C $projectRoot checkout $branch
git -C $projectRoot pull --rebase origin $branch

Write-Host "[2/3] Re-running installer"
& (Join-Path $PSScriptRoot "install-windows.ps1")

Write-Host "[3/3] Update complete"
Write-Host "Start with: .\scripts\start-windows.ps1"
