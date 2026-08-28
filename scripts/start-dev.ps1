# Dev server (local SQLite, uvicorn + frontend build).
param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$DataDir = if ($env:TCGTOOLS_DATA_DIR) { $env:TCGTOOLS_DATA_DIR } else { Join-Path $Root "data" }

$env:TCGTOOLS_DATA_DIR = $DataDir
$env:TCGTOOLS_PORT = "$Port"

if (Test-Path (Join-Path $Root "runtime\venv\Scripts\python.exe")) {
    $py = Join-Path $Root "runtime\venv\Scripts\python.exe"
    $pyArgs = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port", "--reload")
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $py = "py"
    $pyArgs = @("-3.13", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port", "--reload")
} else {
    throw "Python 3.13 nao encontrado. Execute scripts\setup.ps1 primeiro."
}

Write-Host "Iniciando TCG Tools (dev) em http://127.0.0.1:$Port ..." -ForegroundColor Cyan
Write-Host "Dados: $DataDir" -ForegroundColor DarkGray
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
