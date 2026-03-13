$ErrorActionPreference = "Stop"

$ports = @(12888, 12889)

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Host "No listening process found on port $port"
        continue
    }

    $connections |
        Select-Object -ExpandProperty OwningProcess -Unique |
        ForEach-Object {
            Write-Host "Stopping process $($_) on port $port"
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
}

Write-Host "OpenClaw Monitor stop routine completed."
