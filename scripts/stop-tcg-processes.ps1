# Stop TCG Tools launcher and embedded python child processes.
$ErrorActionPreference = "SilentlyContinue"
Stop-Process -Name "TCGTools" -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.ExecutablePath -like '*\TCG Tools\*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1
