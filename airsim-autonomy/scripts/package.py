"""Create a source delivery ZIP; include only the required existing PC module."""
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parents[1]
output = root / 'dist'
output.mkdir(exist_ok=True)
archive = output / 'Mavic2Autonomy-AirSim-source.zip'
excluded = {'.venv', 'vendor', 'downloads', 'environments', 'logs', '__pycache__', 'dist'}
with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
    for path in sorted(root.rglob('*')):
        if path.is_file() and not any(part in excluded for part in path.relative_to(root).parts):
            z.write(path, path.relative_to(root.parent))
    dependency = root.parent / 'pc-control/mission_intelligence.py'
    z.write(dependency, 'pc-control/mission_intelligence.py')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    print(f'{archive}: {len(z.namelist())} files, {archive.stat().st_size} bytes')
