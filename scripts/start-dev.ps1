# Dev server with shared instance mutex (same as TCGTools.exe launcher).
param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$DataDir = Join-Path $env:APPDATA "TCGTools"

. (Join-Path $PSScriptRoot "lib\Instance-Lock.ps1")

if ($Port -le 0) {
    $cfgPath = Join-Path $DataDir "launcher_config.json"
    if (Test-Path $cfgPath) {
        try {
            $Port = [int](Get-Content -Raw $cfgPath | ConvertFrom-Json).port
        } catch {
            $Port = 8000
        }
    } else {
        $Port = 8000
    }
}

if (Test-TCGToolsInstanceRunning) {
    Write-Host "TCG Tools ja esta em execucao nesta sessao de usuario." -ForegroundColor Yellow
    exit 1
}

Enter-TCGToolsInstanceLock
try {
    $env:TCGTOOLS_DATA_DIR = $DataDir
    $env:TCGTOOLS_PORT = "$Port"
    $pyArgs = $null

    if (Test-Path (Join-Path $Root "runtime\venv\Scripts\python.exe")) {
        $py = Join-Path $Root "runtime\venv\Scripts\python.exe"
    } elseif (Test-Path (Join-Path $Root "runtime\python\python.exe")) {
        $py = Join-Path $Root "runtime\python\python.exe"
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $py = "py"
        $pyArgs = @("-3.13", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port")
    } else {
        $py = "python"
    }

    if (-not $pyArgs) {
        $pyArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port")
    }

    Write-Host "Iniciando TCG Tools (dev) na porta $Port..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:$Port"
    Push-Location $Backend
    try {
        if ($py -eq "py") {
            & py @pyArgs
        } else {
            & $py @pyArgs
        }
    } finally {
        Pop-Location
    }
} finally {
    Exit-TCGToolsInstanceLock
}
