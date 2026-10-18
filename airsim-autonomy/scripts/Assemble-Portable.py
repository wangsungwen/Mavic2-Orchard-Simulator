"""Assemble already-built UE4 and PyInstaller outputs; never deletes source files."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'dist/Mavic2Simulator-Orchard-v1-20261018'


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        shutil.copy2(source, target)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--finalize', action='store_true')
    args = parser.parse_args()
    if not args.finalize:
        if DEST.exists():
            raise SystemExit('Destination exists; preserve it or choose a new release path')
        stage = ROOT / 'artifacts/portable-stage/WindowsNoEditor'
        if not (stage / 'Blocks/Binaries/Win64/Blocks.exe').is_file():
            raise SystemExit('Packaged game missing')
        copy(stage, DEST / 'Simulator')
        copy(ROOT / 'artifacts/controller-dist/Mavic2Navigation', DEST / 'Controller')
        copy(ROOT / 'config/settings-mavic2.json', DEST / 'Controller/config/settings-mavic2.json')
        copy(ROOT / 'docs/UE4選點飛行操作.md', DEST / 'docs/UE4選點飛行操作.md')
        copy(ROOT / 'docs/可攜版快速開始.md', DEST / 'README_先讀我.md')
        copy(ROOT / 'docs/山坡柑橘果園原型.md', DEST / 'docs/山坡柑橘果園原型.md')
        copy(ROOT / 'vendor/AirSim/LICENSE', DEST / 'Licenses/AirSim-LICENSE.txt')
        for file in ('point_navigation.py', 'requirements.txt'):
            copy(ROOT / file, DEST / 'Source' / file)
        source = ROOT / 'vendor/AirSim/Unreal/Environments/Blocks'
        for part in ('Source', 'Config'):
            copy(source / part, DEST / 'Source/Blocks' / part)
        copy(ROOT / 'artifacts/Mavic2Navigation.spec', DEST / 'Source/Mavic2Navigation.spec')
        (DEST / 'Start-Navigation.cmd').write_text(
            '@echo off\nsetlocal\ncd /d "%~dp0"\n'
            '"%~dp0Controller\\Mavic2Navigation.exe" --scene Orchard --simulator "%~dp0Simulator\\Blocks\\Binaries\\Win64\\Blocks.exe"\n'
            'if errorlevel 1 pause\n', encoding='ascii')
        shutil.copy2(DEST / 'Start-Navigation.cmd', DEST / 'Start-Orchard.cmd')
        (DEST / 'Start-Blocks.cmd').write_text(
            (DEST / 'Start-Navigation.cmd').read_text(encoding='ascii').replace('--scene Orchard', '--scene Blocks'), encoding='ascii')
        (DEST / 'Check-Runtime.cmd').write_text(
            '@echo off\n"%~dp0Controller\\Mavic2Navigation.exe" --self-test\npause\n', encoding='ascii')
        (DEST / 'Verify-Package.ps1').write_text('''$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $root 'SHA256SUMS.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$count = 0
foreach ($entry in $manifest.PSObject.Properties) {
    $file = Join-Path $root $entry.Name
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing: $($entry.Name)" }
    if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Hash mismatch: $($entry.Name)"
    }
    $count++
}
Write-Host "PASS: $count files verified. Runtime logs are not part of the manifest."
''', encoding='utf-8-sig')
        print(DEST)
        return
    files = [p for p in sorted(DEST.rglob('*')) if p.is_file()
             and p.name != 'SHA256SUMS.json' and 'logs' not in [s.lower() for s in p.relative_to(DEST).parts]]
    manifest = {p.relative_to(DEST).as_posix(): digest(p) for p in files}
    (DEST / 'SHA256SUMS.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    archive = DEST.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=5) as z:
        for p in files + [DEST / 'SHA256SUMS.json']:
            z.write(p, p.relative_to(DEST.parent))
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256.txt').write_text(checksum + '  ' + archive.name + '\n', encoding='ascii')
    print(json.dumps(dict(archive=str(archive), bytes=archive.stat().st_size, files=len(files), sha256=checksum)))


if __name__ == '__main__':
    main()
