# Pester tests for PowerShell modules/scripts
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $Root
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Get-PackageProvider -Name NuGet -ForceBootstrap | Out-Null
Set-PSRepository PSGallery -InstallationPolicy Trusted
Install-Module Pester -MinimumVersion 5.0 -Force -Scope CurrentUser -AllowClobber -SkipPublisherCheck
$result = Invoke-Pester -Path scripts/tests -PassThru
if ($result.FailedCount -gt 0) { throw "Pester: $($result.FailedCount) test(s) failed" }
