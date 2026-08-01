# Shared single-instance lock — same name as launcher (Local\TCGTools_SingleInstance).
# One running instance per Windows user session (multi-user safe).

$Script:TCGToolsMutexName = 'Local\TCGTools_SingleInstance'
$Script:TCGToolsHeldMutex = $null

function Test-TCGToolsInstanceRunning {
    $created = $false
    $m = New-Object System.Threading.Mutex($false, $Script:TCGToolsMutexName, [ref]$created)
    try {
        if (-not $created) { return $true }
        $m.ReleaseMutex()
        return $false
    } finally {
        $m.Dispose()
    }
}

function Enter-TCGToolsInstanceLock {
    if ($Script:TCGToolsHeldMutex) { return }
    $created = $false
    $m = New-Object System.Threading.Mutex($false, $Script:TCGToolsMutexName, [ref]$created)
    if (-not $created) {
        $m.Dispose()
        throw "TCG Tools ja esta em execucao nesta sessao de usuario."
    }
    $Script:TCGToolsHeldMutex = $m
}

function Exit-TCGToolsInstanceLock {
    if (-not $Script:TCGToolsHeldMutex) { return }
    try {
        $Script:TCGToolsHeldMutex.ReleaseMutex()
    } finally {
        $Script:TCGToolsHeldMutex.Dispose()
        $Script:TCGToolsHeldMutex = $null
    }
}

Export-ModuleMember -Function Test-TCGToolsInstanceRunning, Enter-TCGToolsInstanceLock, Exit-TCGToolsInstanceLock
