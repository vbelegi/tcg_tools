# Pester tests for validate-prod-lock.ps1

Describe "Validate-ProdLock" {
    It "accepts pinned lockfile" {
        $ScriptsRoot = Split-Path -Parent $PSScriptRoot
        & (Join-Path $ScriptsRoot "validate-prod-lock.ps1") | Out-Null
    }

    It "rejects unpinned requirements" {
        $ScriptsRoot = Split-Path -Parent $PSScriptRoot
        $bad = Join-Path $env:TEMP "tcg-bad-lock.txt"
        Set-Content -Path $bad -Value "fastapi>=0.1.0"
        { & (Join-Path $ScriptsRoot "validate-prod-lock.ps1") -LockFile $bad } | Should -Throw
        Remove-Item $bad -Force -ErrorAction SilentlyContinue
    }
}
