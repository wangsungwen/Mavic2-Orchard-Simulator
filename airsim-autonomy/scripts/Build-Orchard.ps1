param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_4.27')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$projectDir = Join-Path $root 'vendor/AirSim/Unreal/Environments/Blocks'
$project = Join-Path $projectDir 'Blocks.uproject'
if (Get-Process UE4Editor,UE4Editor-Cmd -ErrorAction SilentlyContinue) {
    throw 'Close UE4 before rebuilding the orchard module.'
}
foreach ($name in @('OrchardScene.h','OrchardScene.cpp')) {
    Copy-Item -LiteralPath (Join-Path $root "src/ue4/$name") -Destination (Join-Path $projectDir "Source/Blocks/$name")
}
$buildCs = Join-Path $projectDir 'Source/Blocks/Blocks.Build.cs'
$content = [IO.File]::ReadAllText($buildCs)
if (-not $content.Contains('"ProceduralMeshComponent"')) {
    [IO.File]::WriteAllText($buildCs, $content.Replace('"UMG"', '"UMG", "ProceduralMeshComponent"'))
}
$definition = Get-Content -LiteralPath $project -Raw | ConvertFrom-Json
foreach ($name in @('ProceduralMeshComponent','PythonScriptPlugin','EditorScriptingUtilities')) {
    $existing = $definition.Plugins | Where-Object Name -eq $name
    if ($existing) { $existing.Enabled = $true }
    else { $definition.Plugins += [pscustomobject]@{Name=$name;Enabled=$true} }
}
[IO.File]::WriteAllText($project, ($definition | ConvertTo-Json -Depth 8))
$build = Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat'
& $build BlocksEditor Win64 Development $project -WaitMutex -NoHotReloadFromIDE -2022
if ($LASTEXITCODE -ne 0) { throw "Orchard C++ build failed: $LASTEXITCODE" }
$editor = Join-Path $EngineRoot 'Engine/Binaries/Win64/UE4Editor-Cmd.exe'
$script = Join-Path $PSScriptRoot 'Create-Orchard.py'
$argsList = @("`"$project`"", "-ExecutePythonScript=`"$script`"", '-unattended', '-nosplash', '-RenderOffscreen')
$started = Get-Date
$process = Start-Process -FilePath $editor -ArgumentList $argsList -WindowStyle Hidden -PassThru -Wait
if ($process.ExitCode -ne 0) { throw "Orchard map generation failed: $($process.ExitCode)" }
$report = Join-Path $root 'artifacts/orchard/scene-build.json'
if (-not (Test-Path -LiteralPath $report) -or (Get-Item -LiteralPath $report).LastWriteTime -lt $started) {
    throw 'Orchard Python script did not complete. Inspect Blocks/Saved/Logs/Blocks.log.'
}
$map = Join-Path $projectDir 'Content/Orchard/Maps/Orchard_Hillside.umap'
if (-not (Test-Path -LiteralPath $map)) { throw 'Orchard map missing.' }
$ini = Join-Path $projectDir 'Config/DefaultGame.ini'
$content = [IO.File]::ReadAllText($ini)
if (-not $content.Contains('/Game/Orchard/Maps/Orchard_Hillside')) {
    Add-Content -LiteralPath $ini -Value "`n[/Script/UnrealEd.ProjectPackagingSettings]`n+MapsToCook=(FilePath=`"/Game/Orchard/Maps/Orchard_Hillside`")`n+DirectoriesToAlwaysCook=(Path=`"/Game/Orchard`")"
}
Write-Host 'Orchard generated. Run Start-Orchard.cmd.'
