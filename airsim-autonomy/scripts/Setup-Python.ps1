$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$python = Join-Path $root '.venv/Scripts/python.exe'
if (-not (Test-Path $python)) {
    & py -3.10 -m venv (Join-Path $root '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Install 64-bit CPython 3.10 first.' }
}
& $python -c 'import sys; assert sys.version_info[:2] == (3,10), sys.version'
if ($LASTEXITCODE -ne 0) { throw 'This environment requires Python 3.10.' }
& $python -m pip install 'pip==24.0' 'setuptools==68.2.2' 'wheel==0.41.3'
if ($LASTEXITCODE -ne 0) { throw 'Bootstrap failed.' }
# AirSim setup imports its own package; dependencies must exist before metadata generation.
& $python -m pip install 'numpy==1.23.5' 'msgpack-python==0.5.6' 'tornado==4.5.3' 'msgpack-rpc-python==0.4.1' 'opencv-contrib-python==4.8.1.78'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $python -m pip install --no-build-isolation -r (Join-Path $root 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'AirSim installation failed.' }
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed.' }
& $python -c 'import airsim; print(airsim.__file__)'
if ($LASTEXITCODE -ne 0) { throw 'Import check failed.' }
