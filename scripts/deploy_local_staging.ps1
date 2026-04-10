param(
    [Parameter(Mandatory = $true)]
    [string]$WorkspacePath,

    [Parameter(Mandatory = $true)]
    [string]$DeployRoot,

    [Parameter(Mandatory = $true)]
    [int]$Port,

    [Parameter(Mandatory = $false)]
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

function Resolve-PythonPath {
    param([string]$PreferredPath)

    if ($PreferredPath -and (Test-Path -Path $PreferredPath)) {
        return (Resolve-Path $PreferredPath).Path
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return "py -3"
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    $candidates = @(
        "$env:USERPROFILE\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
        "$env:USERPROFILE\\AppData\\Local\\Programs\\Python\\Python311\\python.exe",
        "$env:LOCALAPPDATA\\Programs\\Python\\Python312\\python.exe",
        "$env:LOCALAPPDATA\\Programs\\Python\\Python311\\python.exe",
        "$env:ProgramFiles\\Python312\\python.exe",
        "$env:ProgramFiles\\Python311\\python.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path -Path $candidate) {
            return $candidate
        }
    }

    throw "Python executable not found. Set WINDOWS_PYTHON parameter in Jenkins."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PythonCommand,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $false)]
        [string]$WorkingDirectory = ""
    )

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
    }

    try {
        if ($PythonCommand -eq "py -3") {
            & py -3 @Arguments
        } else {
            & $PythonCommand @Arguments
        }

        if ($LASTEXITCODE -ne 0) {
            throw "Python command failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        if ($WorkingDirectory) {
            Pop-Location
        }
    }
}

$pythonCommand = Resolve-PythonPath -PreferredPath $PythonExe
Write-Host "Using Python command: $pythonCommand"

$backendSource = Join-Path $WorkspacePath "backend"
$frontendDistSource = Join-Path $WorkspacePath "frontend\\dist"
$datasetSource = Join-Path $WorkspacePath "online_retail_listing.csv"

if (-not (Test-Path -Path $backendSource)) {
    throw "Backend source folder not found: $backendSource"
}
if (-not (Test-Path -Path $frontendDistSource)) {
    throw "Frontend dist folder not found: $frontendDistSource"
}
if (-not (Test-Path -Path $datasetSource)) {
    throw "Dataset file not found: $datasetSource"
}

New-Item -ItemType Directory -Path $DeployRoot -Force | Out-Null

$backendTarget = Join-Path $DeployRoot "backend"
$frontendTarget = Join-Path $DeployRoot "frontend-dist"
$pidFile = Join-Path $DeployRoot "backend.pid"
$stdoutLog = Join-Path $DeployRoot "backend.stdout.log"
$stderrLog = Join-Path $DeployRoot "backend.stderr.log"

if (Test-Path -Path $backendTarget) {
    Remove-Item -Path $backendTarget -Recurse -Force
}
if (Test-Path -Path $frontendTarget) {
    Remove-Item -Path $frontendTarget -Recurse -Force
}

New-Item -ItemType Directory -Path $backendTarget -Force | Out-Null
New-Item -ItemType Directory -Path $frontendTarget -Force | Out-Null

Copy-Item -Path (Join-Path $backendSource "app") -Destination $backendTarget -Recurse -Force
Copy-Item -Path (Join-Path $backendSource "ml") -Destination $backendTarget -Recurse -Force
Copy-Item -Path (Join-Path $backendSource "requirements.txt") -Destination $backendTarget -Force
Copy-Item -Path $datasetSource -Destination (Join-Path $DeployRoot "online_retail_listing.csv") -Force
Copy-Item -Path (Join-Path $frontendDistSource "*") -Destination $frontendTarget -Recurse -Force

if (Test-Path -Path $pidFile) {
    $existingPid = Get-Content -Path $pidFile -ErrorAction SilentlyContinue
    if ($existingPid) {
        Stop-Process -Id ([int]$existingPid) -Force -ErrorAction SilentlyContinue
    }
    Remove-Item -Path $pidFile -Force -ErrorAction SilentlyContinue
}

$venvPath = Join-Path $backendTarget ".venv"
if (Test-Path -Path $venvPath) {
    Remove-Item -Path $venvPath -Recurse -Force
}

Invoke-Python -PythonCommand $pythonCommand -Arguments @("-m", "venv", ".venv") -WorkingDirectory $backendTarget

$runtimePython = Join-Path $venvPath "Scripts\\python.exe"
if (-not (Test-Path -Path $runtimePython)) {
    throw "Runtime python not found in venv: $runtimePython"
}

Invoke-Python -PythonCommand $runtimePython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -WorkingDirectory $backendTarget
Invoke-Python -PythonCommand $runtimePython -Arguments @("-m", "pip", "install", "-r", "requirements.txt") -WorkingDirectory $backendTarget

if (Test-Path -Path $stdoutLog) {
    Remove-Item -Path $stdoutLog -Force
}
if (Test-Path -Path $stderrLog) {
    Remove-Item -Path $stderrLog -Force
}

$process = Start-Process -FilePath $runtimePython `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port") `
    -WorkingDirectory $backendTarget `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

Set-Content -Path $pidFile -Value $process.Id -NoNewline

$summaryPath = Join-Path $DeployRoot "deployment-summary.txt"
@(
    "Deploy root: $DeployRoot"
    "Backend target: $backendTarget"
    "Frontend target: $frontendTarget"
    "Backend PID: $($process.Id)"
    "Port: $Port"
    "Python command: $pythonCommand"
) | Set-Content -Path $summaryPath

Write-Host "Deployment completed. Backend PID: $($process.Id)."
Write-Host "Frontend static files copied to: $frontendTarget"
