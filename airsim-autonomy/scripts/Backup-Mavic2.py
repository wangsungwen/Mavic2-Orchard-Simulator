"""Create a self-contained model/source backup, excluding engine/plugin code."""
import hashlib
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

root = Path(__file__).resolve().parents[1]
project = root/'vendor/AirSim/Unreal/Environments/Blocks'
parts_dir = root/'fbx/mavic2-separated'
parts = json.loads((parts_dir/'parts.json').read_text())
objects, connections = [], []
header = None
for index, part in enumerate(parts):
    source = (parts_dir/(part['name']+'.fbx')).read_text()
    if header is None:
        header = source.split('Objects: {')[0].replace('Count: 2','Count: 10').replace('ObjectType: "Geometry" {\n  Count: 1','ObjectType: "Geometry" {\n  Count: 5').replace('ObjectType: "Model" {\n  Count: 1','ObjectType: "Model" {\n  Count: 5')
    block = source.split('Objects: {',1)[1].split('\nConnections:',1)[0].rstrip()
    assert block.endswith('}')
    block = block[:-1]
    geometry_id, model_id = 1000+index*2, 1001+index*2
    block = block.replace('Geometry: 1000,',f'Geometry: {geometry_id},').replace('Model: 1001,',f'Model: {model_id},')
    x,y,z = part['pivot_cm']
    block = block.replace('"Lcl Translation", "Lcl Translation", "", "A",0,0,0',f'"Lcl Translation", "Lcl Translation", "", "A",{x:.9g},{-y:.9g},{z:.9g}')
    objects.append(block)
    connections.extend([f' C: "OO",{geometry_id},{model_id}',f' C: "OO",{model_id},0'])
assembly = root/'fbx/Mavic2_Corrected_Assembly.fbx'
assembly.write_text(header+'Objects: {\n'+''.join(objects)+'\n}\nConnections: {\n'+'\n'.join(connections)+'\n}\n',encoding='ascii')
if '--assemble-only' in sys.argv:
    print(assembly)
    raise SystemExit

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
bundle = root/'fbx'/('Mavic2_Corrected_Backup_'+stamp)
bundle.mkdir()
def copy(source, destination):
    target = bundle/destination
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)

shutil.copytree(project/'Content/Mavic2',bundle/'Content/Mavic2')
dependencies = json.loads((root/'artifacts/mavic2/dependencies.json').read_text())
for package in dependencies:
    if package.startswith('/AirSim/'):
        rel = package.removeprefix('/AirSim/')+'.uasset'
        copy(project/'Plugins/AirSim/Content'/rel,Path('AirSimContentDependencies/Content')/rel)
copy(root/'artifacts/mavic2/dependencies.json','dependencies.json')
copy(project/'Plugins/AirSim/AirSim.uplugin','reference/AirSim.uplugin')
copy(project/'Blocks.uproject','reference/Blocks.uproject')
copy(root/'config/settings-mavic2.json','config/settings-mavic2.json')
copy(assembly,'fbx/Mavic2_Corrected_Assembly.fbx')
shutil.copytree(parts_dir,bundle/'fbx/mavic2-separated')
for name in ['ImageToStl.com_DJi+Mavic+2+pro+drone+Rail+2020-1.fbx','DJi Mavic 2 pro drone Rail 2020-1.STL','1-dji-mavic-2-pro-drone-rail-2020-1.snapshot.9.zip']:
    copy(root/'fbx'/name,Path('fbx')/name)
for name in ['Import-Mavic2.py','Import-Mavic2-Rotors.py','Split-Mavic2-Rotors.py','Start-Mavic2.ps1']:
    copy(root/'scripts'/name,Path('scripts')/name)
for name in ['geometry.json','rotor-import.json','rotor-verification.json','rotor-runtime-evidence.txt','rotors-hover.png','rotors-hover.json','assembly-validation.json']:
    copy(root/'artifacts/mavic2'/name,Path('artifacts/mavic2')/name)
copy(root/'docs/Mavic2異地安裝.md','異地安裝說明.md')
copy(root/'scripts/Verify-Mavic2-Backup.ps1','Verify-Backup.ps1')
copy(root/'docs/Mavic2模型匯入結果.md','模型修正及驗證記錄.md')
manifest=[]
for file in sorted(bundle.rglob('*')):
    if file.is_file():
        manifest.append({'path':file.relative_to(bundle).as_posix(),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(bundle/'SHA256SUMS.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
archive = bundle.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for file in sorted(bundle.rglob('*')):
        if file.is_file():
            z.write(file,file.relative_to(bundle).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for item in manifest:
        assert hashlib.sha256(z.read(item['path'])).hexdigest()==item['sha256']
archive.with_suffix('.zip.sha256.txt').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n',encoding='ascii')
result={'folder':str(bundle),'zip':str(archive),'files':len(manifest),'zip_bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(root/'artifacts/mavic2/backup-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
