# Validate requirements-prod.lock format (exact pins only).
param(
    [string]$LockFile = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Path = if ($LockFile) { $LockFile } else { Join-Path $Root "backend\requirements-prod.lock" }

if (-not (Test-Path $Path)) {
    throw "Lockfile nao encontrado: $Path"
}

$lines = Get-Content $Path | Where-Object { $_ -and -not $_.TrimStart().StartsWith("#") }
$bad = @()
foreach ($line in $lines) {
    if ($line -match '[<>]' -or $line -notmatch '^[A-Za-z0-9_.-]+==[0-9]') {
        $bad += $line
    }
}
if ($bad.Count -gt 0) {
    throw "Lockfile deve usar pins exatos (pacote==versao). Invalido:`n$($bad -join "`n")"
}
if ($lines.Count -lt 10) {
    throw "Lockfile parece incompleto ($($lines.Count) pacotes)."
}
Write-Host "Lockfile OK ($($lines.Count) pacotes)." -ForegroundColor Green
