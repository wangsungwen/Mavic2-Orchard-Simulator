param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_4.27')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$project = Join-Path $root 'vendor/AirSim/Unreal/Environments/Blocks/Blocks.uproject'
$ubt = Join-Path $EngineRoot 'Engine/Binaries/DotNET/UnrealBuildTool.exe'
$build = Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat'
$version = Get-Content -LiteralPath (Join-Path $EngineRoot 'Engine/Build/Build.version') -Raw | ConvertFrom-Json
if ($version.MajorVersion -ne 4 -or $version.MinorVersion -ne 27 -or $version.PatchVersion -ne 2) {
    throw 'This project requires Unreal Engine 4.27.2.'
}
foreach ($path in @($project, $ubt, $build)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing: $path" }
}
& $ubt -projectfiles "-project=$project" -game -engine -progress -2022
if ($LASTEXITCODE -ne 0) { throw "Project generation failed: $LASTEXITCODE" }
& $build BlocksEditor Win64 Development $project -WaitMutex -NoHotReloadFromIDE -2022
if ($LASTEXITCODE -ne 0) { throw "Blocks build failed: $LASTEXITCODE" }
foreach ($relative in @('Binaries/Win64/UE4Editor-Blocks.dll', 'Plugins/AirSim/Binaries/Win64/UE4Editor-AirSim.dll')) {
    if (-not (Test-Path -LiteralPath (Join-Path (Split-Path $project -Parent) $relative))) {
        throw "Build output missing: $relative"
    }
}
Write-Host 'BlocksEditor and AirSim plugin built successfully. Runtime verification is still required.'
