# Full Windows test suite (backend + frontend + launcher + pester + lockfile validation)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
& (Join-Path $PSScriptRoot "run-backend-tests.ps1")
& (Join-Path $PSScriptRoot "run-frontend-tests.ps1")
& (Join-Path $PSScriptRoot "run-launcher-tests.ps1")
& (Join-Path $Root "scripts\validate-prod-lock.ps1")
& (Join-Path $PSScriptRoot "run-pester-tests.ps1")
