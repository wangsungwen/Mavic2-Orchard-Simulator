param([Parameter(Mandatory=$true)][string]$BinaryDirectory)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$destination = (Resolve-Path -LiteralPath $BinaryDirectory).Path
$sceneRoot = [IO.Path]::GetFullPath((Join-Path $root 'environments')) + [IO.Path]::DirectorySeparatorChar
if (-not $destination.StartsWith($sceneRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Local runtime deployment is limited to this package environments directory.'
}
$libraries = @{
    'X3DAudio1_7.dll' = 'Feb2010_X3DAudio_x64.cab'
    'XAPOFX1_5.dll' = 'Jun2010_XAudio_x64.cab'
    'D3DCompiler_43.dll' = 'Jun2010_D3DCompiler_43_x64.cab'
    'xinput1_3.dll' = 'Apr2007_xinput_x64.cab'
}
$missing = @($libraries.Keys | Where-Object {
    -not (Test-Path -LiteralPath (Join-Path $destination $_)) -and
    -not (Test-Path -LiteralPath (Join-Path ([Environment]::SystemDirectory) $_))
})
if ($missing.Count -eq 0) { Write-Host 'Legacy DirectX libraries are available.'; return }
$downloads = Join-Path $root 'downloads'
New-Item -ItemType Directory -Force $downloads | Out-Null
$installer = Join-Path $downloads 'directx_Jun2010_redist.exe'
if (-not (Test-Path -LiteralPath $installer)) {
    $partial = "$installer.partial"
    & curl.exe -L --fail --retry 2 --output $partial 'https://download.microsoft.com/download/8/4/a/84a35bf1-dafe-4ae8-82af-ad2ae20b6b14/directx_Jun2010_redist.exe'
    if ($LASTEXITCODE -ne 0) { throw 'Microsoft DirectX package download failed.' }
    Move-Item -LiteralPath $partial -Destination $installer
}
$signature = Get-AuthenticodeSignature -LiteralPath $installer
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation') {
    throw 'DirectX package must have a valid Microsoft signature.'
}
$expanded = Join-Path $downloads 'directx-jun2010'
New-Item -ItemType Directory -Force $expanded | Out-Null
$process = Start-Process -FilePath $installer -ArgumentList @('/Q', "/T:`"$expanded`"") -WindowStyle Hidden -PassThru
$process.WaitForExit()
if ($process.ExitCode -ne 0) { throw "DirectX extraction failed: $($process.ExitCode)" }
# Extract only the required x64 DLLs beside Blocks.exe. No DXSETUP, system changes or COM registration.
foreach ($name in $missing) {
    & expand.exe (Join-Path $expanded $libraries[$name]) "-F:$name" $destination
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $destination $name))) {
        throw "Failed to extract $name"
    }
}
Write-Host 'Required legacy DirectX DLLs deployed locally beside Blocks.exe.'
