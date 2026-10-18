import json
import os
import unreal

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
registry = unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
options = unreal.AssetRegistryDependencyOptions()
options.include_hard_package_references = True
options.include_soft_package_references = True
seen = set()
queue = ['/Game/Mavic2/Blueprints/BP_Mavic2']
while queue:
    path = queue.pop()
    if path in seen:
        continue
    seen.add(path)
    if path.startswith(('/Game/', '/AirSim/')):
        queue.extend(str(p) for p in registry.get_dependencies(path, options))
with open(os.path.join(root,'artifacts/mavic2/dependencies.json'),'w') as f:
    json.dump(sorted(seen), f, indent=2)
unreal.log('DEPENDENCIES_COMPLETE '+str(len(seen)))
