param(
    [string]$EngineRoot = 'C:\Program Files\Epic Games\UE_4.27',
    [switch]$Editor,
    [ValidateSet('Blocks','Orchard')][string]$Scene = 'Blocks'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$project = Join-Path $root 'vendor/AirSim/Unreal/Environments/Blocks/Blocks.uproject'
$settings = Join-Path $root 'config/settings-mavic2.json'
$engineExe = Join-Path $EngineRoot 'Engine/Binaries/Win64/UE4Editor.exe'
$pawn = Join-Path (Split-Path $project -Parent) 'Content/Mavic2/Blueprints/BP_Mavic2.uasset'
foreach ($path in @($project, $settings, $engineExe, $pawn)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing: $path" }
}
if (Get-NetTCPConnection -LocalPort 41451 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 41451 is in use. Close the running simulator before starting Mavic 2.'
}
$launchArgs = @("`"$project`"")
if ($Scene -eq 'Orchard') {
    $map = Join-Path (Split-Path $project -Parent) 'Content/Orchard/Maps/Orchard_Hillside.umap'
    if (-not (Test-Path -LiteralPath $map)) { throw 'Run scripts/Build-Orchard.ps1 first.' }
    $launchArgs += '/Game/Orchard/Maps/Orchard_Hillside'
}
$launchArgs += @("-settings=`"$settings`"", '-nosplash')
if (-not $Editor) {
    $launchArgs += @('-game', '-windowed', '-ResX=1280', '-ResY=720')
}
# The user requested the UE4 model; this is its interactive viewport/editor.
$process = Start-Process -FilePath $engineExe -ArgumentList $launchArgs -WorkingDirectory (Split-Path $project -Parent) -PassThru
Write-Host "Mavic 2 UE4 process started. PID: $($process.Id)"
if ($Editor) { Write-Host 'Open Content/Mavic2/Blueprints/BP_Mavic2, or press Play to simulate.' }
else { Write-Host 'The project uses MavicSim; existing fly.py commands remain compatible.' }
