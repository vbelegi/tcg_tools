# Frontend tests + build
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location (Join-Path $Root "frontend")
py -3.13 -m pip install -q -e "$Root\backend[dev]"
npm ci
npm run test:coverage
npm run build
