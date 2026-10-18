$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $root 'SHA256SUMS.json') -Raw | ConvertFrom-Json
foreach ($item in $manifest) {
    $path = Join-Path $root $item.path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing: $($item.path)" }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $item.sha256) { throw "Hash mismatch: $($item.path)" }
}
Write-Host "PASS: $($manifest.Count) files verified."
