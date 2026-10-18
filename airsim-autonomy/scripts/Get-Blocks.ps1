$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$downloads = Join-Path $root 'downloads'
$destination = Join-Path $root 'environments/Blocks'
if (Test-Path $destination) {
    $existing = @(Get-ChildItem -LiteralPath $destination -Recurse -Filter 'Blocks.exe' |
        Where-Object { $_.Directory.Name -eq 'WindowsNoEditor' })
    if ($existing.Count -eq 1 -and (Test-Path -LiteralPath (Join-Path $existing[0].Directory.FullName 'Blocks/Binaries/Win64/Blocks.exe'))) {
        Write-Host 'Blocks is already extracted. Reusing existing installation:'
        Write-Host $existing[0].FullName
        Write-Host 'Next: run scripts/Start-Simulator.ps1 without -Exe.'
        return
    }
    throw "Destination exists but a unique complete Blocks executable pair was not found: $destination. Inspect the extraction before retrying."
}
New-Item -ItemType Directory -Force $downloads | Out-Null
$zip = Join-Path $downloads 'Blocks-v1.8.1-windows.zip'
$partial = "$zip.partial"
if (-not (Test-Path $zip)) {
    Invoke-WebRequest -Uri 'https://github.com/microsoft/AirSim/releases/download/v1.8.1-windows/Blocks.zip' -OutFile $partial
    Move-Item -LiteralPath $partial -Destination $zip
}
# Local integrity record, not an independently published upstream signature.
Get-FileHash -Algorithm SHA256 -LiteralPath $zip | Format-List | Out-File (Join-Path $downloads 'Blocks.sha256.txt')
Expand-Archive -LiteralPath $zip -DestinationPath $destination
Get-ChildItem -LiteralPath $destination -Recurse -Filter '*.exe' | Select-Object FullName
Write-Host 'Download complete. Launch the top-level Blocks.exe using Start-Simulator.ps1.'
