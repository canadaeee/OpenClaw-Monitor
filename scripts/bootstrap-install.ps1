function Install-OpenClawMonitor {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoUrl,
        [string]$Branch = "main",
        [string]$TargetDir = "$HOME\\OpenClaw-Monitor"
    )

    $ErrorActionPreference = "Stop"

    git --version | Out-Null

    if (Test-Path (Join-Path $TargetDir ".git")) {
        Write-Host "Updating existing repository in $TargetDir"
        git -C $TargetDir fetch origin $Branch
        git -C $TargetDir checkout $Branch
        git -C $TargetDir pull --ff-only origin $Branch
    }
    else {
        Write-Host "Cloning $RepoUrl into $TargetDir"
        git clone --branch $Branch $RepoUrl $TargetDir
    }

    & (Join-Path $TargetDir "scripts\\install-windows.ps1")
}

Write-Host "Use:"
Write-Host "  Install-OpenClawMonitor -RepoUrl https://github.com/<owner>/<repo>.git"
