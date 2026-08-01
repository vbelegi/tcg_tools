# Smoke test: staging layout serves /api/v1/health
param(
    [string]$StagingDir = "",
    [int]$Port = 8765,
    [int]$TimeoutSec = 45
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Staging = if ($StagingDir) { $StagingDir } else { Join-Path $Root "dist\staging" }
$Backend = Join-Path $Staging "backend"
$Python = Join-Path $Staging "runtime\python\python.exe"
$DataDir = Join-Path $env:TEMP "tcg_tools_smoke_$(Get-Random)"
$HealthUrl = "http://127.0.0.1:$Port/api/v1/health"

if (-not (Test-Path $Python)) {
    throw "Python embeddable nao encontrado: $Python (execute build-release.ps1 primeiro)"
}
if (-not (Test-Path $Backend)) {
    throw "Backend staging nao encontrado: $Backend"
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$env:TCGTOOLS_DATA_DIR = $DataDir
$env:TCGTOOLS_PORT = "$Port"

$proc = Start-Process -FilePath $Python -ArgumentList @(
    "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port"
) -WorkingDirectory $Backend -PassThru -WindowStyle Hidden

try {
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    $ok = $false
    while ((Get-Date) -lt $deadline) {
        if ($proc.HasExited) {
            throw "uvicorn encerrou prematuramente (exit $($proc.ExitCode))"
        }
        try {
            $resp = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 3
            if ($resp.StatusCode -eq 200 -and $resp.Content -match '"app"\s*:\s*"tcg_tools"') {
                $ok = $true
                break
            }
        } catch {
            Start-Sleep -Milliseconds 400
        }
    }
    if (-not $ok) {
        throw "Timeout aguardando health em $HealthUrl"
    }
    Write-Host "Smoke staging OK: $HealthUrl" -ForegroundColor Green
} finally {
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item $DataDir -Recurse -Force -ErrorAction SilentlyContinue
}
