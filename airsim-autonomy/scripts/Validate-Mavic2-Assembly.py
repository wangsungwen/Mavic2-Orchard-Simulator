import json
import os
import unreal
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
task = unreal.AssetImportTask()
task.filename = os.path.join(root,'fbx/Mavic2_Corrected_Assembly.fbx')
task.destination_path = '/Game/Mavic2BackupValidation'
task.destination_name = 'AssemblyValidation'
task.automated = True
task.save = False
options = unreal.FbxImportUI()
options.automated_import_should_detect_type = False
options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
options.import_materials = False
options.import_textures = False
options.static_mesh_import_data.combine_meshes = True
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
assert len(task.imported_object_paths)==1
mesh = unreal.load_asset(task.imported_object_paths[0])
vertices, triangles, *_ = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh,0,0)
b = mesh.get_bounds()
extents = [b.box_extent.x,b.box_extent.y,b.box_extent.z]
assert all(abs(a-e)<0.01 for a,e in zip(extents,[20.899321,23.434959,4.941842])),extents
assert len(triangles)//3 == 10970, len(triangles)//3
report={'imported_in':'UE4.27.2','triangles':len(triangles)//3,'box_extent_cm':extents,'origin_cm':[b.origin.x,b.origin.y,b.origin.z],'passed':True}
json.dump(report,open(os.path.join(root,'artifacts/mavic2/assembly-validation.json'),'w'),indent=2)
unreal.log('ASSEMBLY_VALIDATED '+json.dumps(report))
