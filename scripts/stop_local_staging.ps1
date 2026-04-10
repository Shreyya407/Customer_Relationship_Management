param(
    [Parameter(Mandatory = $true)]
    [string]$DeployRoot
)

$ErrorActionPreference = "Stop"
$pidFile = Join-Path $DeployRoot "backend.pid"

if (-not (Test-Path -Path $pidFile)) {
    Write-Host "No running staged backend detected (pid file not found)."
    exit 0
}

$pidText = Get-Content -Path $pidFile -ErrorAction SilentlyContinue
if (-not $pidText) {
    Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
    Write-Host "Pid file was empty and has been removed."
    exit 0
}

$pid = [int]$pidText
Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
Write-Host "Stopped staged backend process: $pid"
