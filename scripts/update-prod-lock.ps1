# Regenerate requirements-prod.lock with exact pins from current pip install.
param(
    [string]$Output = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Out = if ($Output) { $Output } else { Join-Path $Backend "requirements-prod.lock" }

$packages = @(
    "alembic", "annotated-types", "anyio", "bcrypt", "click", "colorama", "fastapi", "greenlet",
    "h11", "httptools", "idna", "Mako", "MarkupSafe", "pillow", "pymysql", "pydantic", "pydantic-core",
    "pydantic-settings", "python-dotenv", "python-multipart", "SQLAlchemy", "starlette",
    "typing-extensions", "uvicorn", "watchfiles", "websockets"
)

Push-Location $Backend
py -3.13 -m pip install -q -e .
$freeze = py -3.13 -m pip freeze
Pop-Location

$map = @{}
foreach ($line in $freeze) {
    if ($line -match '^([^=]+)==(.+)$') {
        $map[$Matches[1].ToLower().Replace("_", "-")] = $line
    }
}

$header = @(
    "# Production dependencies - exact pins for reproducible offline embeddable install.",
    "# Regenerate: ./scripts/update-prod-lock.ps1",
    "# Validate:  ./scripts/validate-prod-lock.ps1",
    ""
)
$outLines = $header + @()
foreach ($pkg in $packages) {
    $key = $pkg.ToLower()
    if (-not $map.ContainsKey($key)) {
        throw "Pacote ausente no freeze: $pkg"
    }
    $outLines += $map[$key]
}
Set-Content -Path $Out -Value ($outLines -join "`n") -NoNewline
Write-Host "Gerado: $Out" -ForegroundColor Green
