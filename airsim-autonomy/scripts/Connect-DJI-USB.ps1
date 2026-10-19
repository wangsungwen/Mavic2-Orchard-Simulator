param([string]$Adb = 'adb', [string]$Serial)
$ErrorActionPreference = 'Stop'
# Only establish a local status transport; never install, launch or control aircraft.
$lines = & $Adb devices
if ($LASTEXITCODE -ne 0) { throw 'adb devices failed; install Android platform-tools or pass -Adb.' }
$devices = @($lines | Where-Object { $_ -match '^\S+\s+device$' } | ForEach-Object { ($_ -split '\s+')[0] })
if ($Serial) {
    if ($Serial -notin $devices) { throw 'Selected device is absent or USB debugging is not authorized.' }
} else {
    if ($devices.Count -ne 1) { throw 'Require exactly one authorized device, or pass -Serial explicitly.' }
    $Serial = $devices[0]
}
& $Adb -s $Serial forward tcp:8865 tcp:8865
if ($LASTEXITCODE -ne 0) { throw 'Control-port forwarding failed.' }
Write-Host 'Ready: HOST 127.0.0.1. Open Mavic Dual Joystick APP and enter its six-digit code in the monitor.'
Write-Host 'No aircraft command sent. This script only forwards status port 8865.'
