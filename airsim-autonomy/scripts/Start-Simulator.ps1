param([string]$Exe)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if (-not $Exe) {
    $candidates = @(Get-ChildItem -LiteralPath (Join-Path $root 'environments/Blocks') -Recurse -Filter 'Blocks.exe' -ErrorAction SilentlyContinue |
        Where-Object { $_.Directory.Name -eq 'WindowsNoEditor' })
    if ($candidates.Count -ne 1) {
        throw 'Expected one top-level Blocks.exe. Run Get-Blocks.ps1 first, or provide -Exe with its actual full path.'
    }
    $Exe = $candidates[0].FullName
}
if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) {
    throw "Executable not found: $Exe. For downloaded Blocks, rerun this script without -Exe to detect the path automatically."
}
$resolvedExe = (Resolve-Path -LiteralPath $Exe).Path
# The top-level Unreal bootstrapper checks system prerequisites. Use the actual
# packaged binary so project-local DirectX DLLs can satisfy its dependencies.
if ((Split-Path (Split-Path $resolvedExe -Parent) -Leaf) -eq 'WindowsNoEditor' -and
    (Split-Path $resolvedExe -Leaf) -eq 'Blocks.exe') {
    $native = Join-Path (Split-Path $resolvedExe -Parent) 'Blocks/Binaries/Win64/Blocks.exe'
    if (-not (Test-Path -LiteralPath $native)) { throw "Incomplete Blocks extraction: $native" }
    $resolvedExe = (Resolve-Path -LiteralPath $native).Path
}
$settings = (Resolve-Path -LiteralPath (Join-Path $root 'config/settings.json')).Path
if ([IO.Path]::GetExtension($resolvedExe) -ne '.exe') { throw 'Supply the packaged scene .exe.' }
if (Get-NetTCPConnection -LocalPort 41451 -State Listen -ErrorAction SilentlyContinue) {
    Write-Host 'Port 41451 already has a listener. Run fly.py status to verify the existing simulator.'
    return
}
if ((Split-Path $resolvedExe -Leaf) -eq 'Blocks.exe') {
    & (Join-Path $PSScriptRoot 'Setup-BlocksRuntime.ps1') -BinaryDirectory (Split-Path $resolvedExe -Parent)
}
# This is the interactive simulator requested by the user; keep its window visible.
Write-Host "Starting: $resolvedExe"
$process = Start-Process -FilePath $resolvedExe -WorkingDirectory (Split-Path $resolvedExe -Parent) -ArgumentList @("-settings=`"$settings`"", '-windowed', '-ResX=1280', '-ResY=720') -PassThru
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
    $process.Refresh()
    if ($process.HasExited) { throw "Simulator exited with code $($process.ExitCode). Check runtime DLLs and scene logs." }
    if (Get-NetTCPConnection -LocalPort 41451 -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "AirSim TCP listener ready. PID: $($process.Id). Next: run fly.py status."
        return
    }
    Start-Sleep -Seconds 1
}
throw 'Simulator process started but port 41451 is not ready after 60 seconds. Check its window for errors.'
