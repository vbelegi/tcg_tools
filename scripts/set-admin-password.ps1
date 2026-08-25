# Define/atualiza senha do admin no SQLite (usado pelo instalador).
param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,
    [string]$Password,
    [string]$PasswordFile
)

$ErrorActionPreference = "Stop"
$Python = Join-Path $InstallDir "runtime\python\python.exe"
$Backend = Join-Path $InstallDir "backend"
if (-not (Test-Path $Python)) { throw "Python nao encontrado: $Python" }
if (-not (Test-Path $Backend)) { throw "Backend nao encontrado: $Backend" }

if ($PasswordFile) {
    if (-not (Test-Path $PasswordFile)) { throw "Arquivo de senha nao encontrado." }
    $Password = [System.IO.File]::ReadAllText($PasswordFile).TrimEnd("`r", "`n")
}
if (-not $Password) { throw "Senha nao informada." }

$DataDir = Join-Path $env:APPDATA "TCGTools"
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

$env:TCGTOOLS_DATA_DIR = $DataDir
$env:TCGTOOLS_SET_ADMIN_PASSWORD = $Password
Push-Location $Backend
try {
    & $Python -m app.scripts.set_admin_password
    if ($LASTEXITCODE -ne 0) { throw "Falha ao gravar senha do admin (exit $LASTEXITCODE)." }
}
finally {
    Pop-Location
    Remove-Item Env:TCGTOOLS_SET_ADMIN_PASSWORD -ErrorAction SilentlyContinue
}
