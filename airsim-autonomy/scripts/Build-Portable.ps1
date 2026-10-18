param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_4.27')
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
$project = Join-Path $root 'vendor\AirSim\Unreal\Environments\Blocks\Blocks.uproject'
$stage = Join-Path $root 'artifacts\portable-stage'
Push-Location $root
try {
    & (Join-Path $EngineRoot 'Engine\Build\BatchFiles\RunUAT.bat') BuildCookRun "-project=$project" -noP4 -platform=Win64 -clientconfig=Development -build -cook -stage -pak -archive "-archivedirectory=$stage" -prereqs -utf8output
    if ($LASTEXITCODE -ne 0) { throw 'UE4 build failed' }
    # Build dependency: PyInstaller 6.16.0 installed in this source environment.
    & $python -m PyInstaller --noconfirm --onedir --name Mavic2Navigation --distpath artifacts\controller-dist --workpath artifacts\controller-build --specpath artifacts --exclude-module matplotlib --exclude-module tkinter --exclude-module IPython --collect-all msgpackrpc --hidden-import tornado.platform.asyncio point_navigation.py
    if ($LASTEXITCODE -ne 0) { throw 'Controller build failed' }
    & $python scripts\Assemble-Portable.py
    if ($LASTEXITCODE -ne 0) { throw 'Assembly failed; existing release is intentionally preserved' }
    Write-Host 'Assembled. Run relocation validation before finalizing the release ZIP.'
} finally { Pop-Location }
