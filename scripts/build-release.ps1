# TCG Tools — build release installer (Windows)
param(
    [switch]$SkipTests,
    [switch]$SkipInno,
    [string]$OutputDir = "",
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Launcher = Join-Path $Root "launcher"
$Dist = if ($OutputDir) { $OutputDir } else { Join-Path $Root "dist" }
$Staging = Join-Path $Dist "staging"
$Runtime = Join-Path $Staging "runtime"

. (Join-Path $PSScriptRoot "lib\Embed-Python.ps1")

function Get-ProjectVersion {
    param([string]$PyProjectPath)
    $content = Get-Content $PyProjectPath -Raw
    if ($content -match 'version\s*=\s*"([^"]+)"') {
        return $Matches[1]
    }
    throw "Versao nao encontrada em pyproject.toml"
}

$Version = if ($Version) { $Version } else { Get-ProjectVersion (Join-Path $Backend "pyproject.toml") }
Write-Host "TCG Tools release build v$Version" -ForegroundColor Cyan

if (-not $SkipTests) {
    Write-Host "Backend tests..."
    Push-Location $Backend
    py -3.13 -m pytest tests/ -q --cov=app --cov-fail-under=80
    Pop-Location

    Write-Host "Frontend tests..."
    Push-Location $Frontend
    npm ci 2>$null; if ($LASTEXITCODE -ne 0) { npm install }
    npm run test:coverage
    Pop-Location

    if (Get-Command go -ErrorAction SilentlyContinue) {
        Write-Host "Launcher tests..."
        Push-Location $Launcher
        go test ./... -coverprofile=coverage.out
        $line = go tool cover -func coverage.out | Select-String "total:"
        if ($line -match "(\d+\.\d+)%") {
            $pct = [double]$Matches[1]
            if ($pct -lt 80) { throw "Launcher coverage ${pct}% below 80%" }
        }
        Pop-Location
    } else {
        Write-Host "AVISO: Go nao encontrado; pulando testes do launcher (CI deve executar)." -ForegroundColor Yellow
    }
}

Write-Host "Frontend build..."
py -3.13 -m pip install -q -e "${Backend}[dev]"
Push-Location $Frontend
npm ci 2>$null; if ($LASTEXITCODE -ne 0) { npm install }
npm run build
if ($LASTEXITCODE -ne 0) { throw "Frontend build failed." }
Pop-Location

if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Staging | Out-Null
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null

Write-Host "Python embeddable + deps..."
& (Join-Path $PSScriptRoot "validate-prod-lock.ps1")
$PyExe = Install-EmbedPython -RuntimeDir $Runtime
if ($PyExe -is [array]) { $PyExe = $PyExe[-1] }
$LockFile = Join-Path $Backend "requirements-prod.lock"
Push-Location $Backend
& $PyExe -m pip install --upgrade pip 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
if (-not (Test-Path $LockFile)) {
    throw "requirements-prod.lock nao encontrado (execute validate-prod-lock.ps1)."
}
& $PyExe -m pip install -r $LockFile
if ($LASTEXITCODE -ne 0) { throw "pip install -r requirements-prod.lock failed." }
Pop-Location

Write-Host "Copiando backend..."
$BackendDest = Join-Path $Staging "backend"
New-Item -ItemType Directory -Force -Path $BackendDest | Out-Null
$BackendItems = @("app", "alembic", "config", "alembic.ini", "pyproject.toml")
foreach ($item in $BackendItems) {
    $src = Join-Path $Backend $item
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $BackendDest $item) -Recurse -Force
    }
}

Write-Host "Copiando frontend dist..."
$FeDest = Join-Path $Staging "frontend\dist"
New-Item -ItemType Directory -Force -Path (Split-Path $FeDest) | Out-Null
Copy-Item (Join-Path $Frontend "dist") $FeDest -Recurse -Force

Copy-Item (Join-Path $PSScriptRoot "stop-tcg-processes.ps1") (Join-Path $Staging "stop-tcg-processes.ps1") -Force
Copy-Item (Join-Path $PSScriptRoot "set-admin-password.ps1") (Join-Path $Staging "set-admin-password.ps1") -Force

Write-Host "Compilando launcher..."
if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    throw "Go compiler necessario para build do launcher."
}
Push-Location $Launcher
go mod tidy
$IconIco = Join-Path $Launcher "internal\app\assets\icon.ico"
if (-not (Test-Path $IconIco)) {
    throw "Icone do launcher nao encontrado: $IconIco"
}
# Incorpora icon.ico nos recursos PE do .exe (atalhos / Explorer). go:embed sozinho so alimenta a bandeja.
$Syso = Join-Path $Launcher "rsrc_windows_amd64.syso"
Write-Host "Gerando recurso de icone Windows ($Syso)..."
go run github.com/akavel/rsrc@v0.10.2 -arch amd64 -ico $IconIco -o $Syso
if ($LASTEXITCODE -ne 0) { throw "Falha ao gerar rsrc_windows_amd64.syso (icone do exe)." }
if (-not (Test-Path $Syso)) { throw "rsrc_windows_amd64.syso nao foi criado." }
go build -ldflags "-H windowsgui -s -w" -o (Join-Path $Staging "TCGTools.exe") .
Pop-Location

Set-Content -Path (Join-Path $Staging "VERSION.txt") -Value $Version -NoNewline

$SetupExe = Join-Path $Dist "TCGTools-$Version-setup.exe"
if (-not $SkipInno) {
    $Iscc = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $Iscc) {
        throw "Inno Setup 6 (ISCC.exe) nao encontrado."
    }
    & $Iscc "/DAppVersion=$Version" "/DStagingDir=$Staging" "/DOutputDir=$Dist" (Join-Path $PSScriptRoot "installer.iss")
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup compile failed (exit $LASTEXITCODE)." }
    if (-not (Test-Path $SetupExe)) { throw "Instalador nao gerado: $SetupExe" }
    Write-Host "Instalador: $SetupExe" -ForegroundColor Green
} else {
    Write-Host "Staging pronto: $Staging" -ForegroundColor Green
}

Write-Host "Build release concluido." -ForegroundColor Green
