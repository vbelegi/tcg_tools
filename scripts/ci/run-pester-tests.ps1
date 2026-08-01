# Pester tests for PowerShell modules/scripts
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser
Set-PSRepository PSGallery -InstallationPolicy Trusted
Install-Module Pester -MinimumVersion 5.0 -Force -Scope CurrentUser
$result = Invoke-Pester -Path scripts/tests -PassThru
if ($result.FailedCount -gt 0) { throw "Pester: $($result.FailedCount) test(s) failed" }
