# Launcher Go tests — per-package coverage gate (testable packages per launcher/README.md).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location (Join-Path $Root "launcher")
go mod tidy

$packages = @(
    @{ Path = "./internal/config"; Min = 80 },
    @{ Path = "./internal/process"; Min = 48 },
    @{ Path = "./internal/registry"; Min = 80 },
    @{ Path = "./internal/instance"; Min = 55 },
    @{ Path = "./internal/app"; Min = 5 },
    @{ Path = "./internal/tray"; Min = 5 }
)

foreach ($entry in $packages) {
    $pkg = $entry.Path
    $min = $entry.Min
    $name = $pkg -replace '^\./', ''
    Write-Host "Testing $pkg ..."
    $output = go test $pkg -covermode=atomic 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        Write-Host $output
        throw "go test failed for $pkg"
    }
    if ($output -match 'coverage:\s*(\d+\.\d+)%') {
        $pct = [double]$Matches[1]
        Write-Host "  ${name}: ${pct}%"
        if ($pct -lt $min) { throw "${name} coverage ${pct}% below ${min}%" }
    } else {
        throw "Could not parse coverage for $pkg"
    }
}

Write-Host "Launcher coverage gate passed." -ForegroundColor Green
