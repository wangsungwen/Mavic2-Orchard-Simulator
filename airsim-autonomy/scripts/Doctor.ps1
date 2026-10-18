$root = Split-Path $PSScriptRoot -Parent
Write-Host 'Python installations:'
& py --list-paths
Write-Host 'Graphics and RAM (may be unavailable under restricted permissions):'
try {
    Get-CimInstance Win32_VideoController -ErrorAction Stop | Select-Object Name,DriverVersion | Format-List | Out-Host
    Get-CimInstance Win32_ComputerSystem -ErrorAction Stop | Select-Object @{Name='RAM_GiB';Expression={[math]::Round($_.TotalPhysicalMemory/1GB,1)}} | Format-List | Out-Host
} catch { Write-Warning $_ }
Write-Host 'UE installations under default directory:'
Get-ChildItem 'C:/Program Files/Epic Games' -ErrorAction SilentlyContinue | Select-Object Name
$python = Join-Path $root '.venv/Scripts/python.exe'
if (Test-Path $python) {
    & $python -c 'import sys, airsim; print(sys.version); print(airsim.__file__)'
} else { Write-Warning 'Run Setup-Python.ps1.' }
Write-Host 'AirSim TCP listener:'
Get-NetTCPConnection -LocalPort 41451 -State Listen -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess | Format-Table | Out-Host
