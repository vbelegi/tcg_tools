# TCG Tools — setup inicial (dev local, Windows)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Runtime = Join-Path $Root "runtime"

Write-Host "TCG Tools — Setup (dev)" -ForegroundColor Cyan

function Install-BackendDeps {
    param([string]$PythonExe)
    Set-Location $Backend
    if ($PythonExe -match " ") {
        & py -3.13 -m pip install -e ".[dev]"
    } else {
        & $PythonExe -m pip install -e ".[dev]"
    }
    if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar dependencias Python." }
}

$uv = Get-Command uv -ErrorAction SilentlyContinue

if ($uv) {
    Write-Host "Usando uv para ambiente Python 3.13..."
    New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
    Set-Location $Backend
    uv venv (Join-Path $Runtime "venv") --python 3.13
    $PythonExe = Join-Path $Runtime "venv\Scripts\python.exe"
    uv pip install -e ".[dev]" --python $PythonExe
} else {
    $py313 = $null
    try {
        $null = & py -3.13 -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $py313 = "py -3.13" }
    } catch { }

    if ($py313) {
        Write-Host "Usando Python 3.13 (py -3.13)..."
        Install-BackendDeps -PythonExe $py313
    } else {
        throw "Python 3.13 necessario. Instale via python.org ou use 'uv' (https://docs.astral.sh/uv/)."
    }
}

Write-Host "Build frontend..."
Set-Location $Frontend
if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm ci 2>$null; if ($LASTEXITCODE -ne 0) { npm install }
    npm run build
} else {
    Write-Host "AVISO: npm nao encontrado. Instale Node.js e execute 'npm run build' em frontend/" -ForegroundColor Yellow
}

$DataDir = if ($env:TCGTOOLS_DATA_DIR) { $env:TCGTOOLS_DATA_DIR } else { Join-Path $Root "data" }
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "logs") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DataDir "exports") | Out-Null

Write-Host "Setup concluido."
Write-Host "Defina a senha do admin (dev, login admin@local):" -ForegroundColor Cyan
Write-Host "  `$env:TCGTOOLS_DATA_DIR='$DataDir'; cd backend; py -3.13 -m app.scripts.set_admin_password --password admin123"
Write-Host "Use 'scripts\Iniciar TCG Tools.bat' para iniciar." -ForegroundColor Green
