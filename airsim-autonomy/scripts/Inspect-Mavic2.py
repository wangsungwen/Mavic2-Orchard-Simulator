"""Run with UE4Editor-Cmd -run=pythonscript -script=..."""
import json
import os
import unreal

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
report = {}
source = "/AirSim/Blueprints/BP_FlyingPawn"
bp = unreal.load_asset(source)
report['blueprint'] = str(bp)
cls = unreal.EditorAssetLibrary.load_blueprint_class(source)
report['class'] = str(cls)
for suffix in [":BodyMesh_GEN_VARIABLE", ":BodyMesh"]:
    path = cls.get_path_name() + suffix
    obj = unreal.load_object(None, path)
    report[path] = str(obj)
    if obj:
        report['body_mesh'] = str(obj.get_editor_property('static_mesh'))
        report['body_transform'] = str(obj.get_editor_property('relative_scale3d'))
report['components'] = []
for name in ['BodyMesh', 'Prop0', 'Prop1', 'Prop2', 'Prop3', 'FrontCenterCamera', 'FrontLeftCamera', 'FrontRightCamera', 'BackCenterCamera', 'BottomCenterCamera', 'Rotation0']:
    c = unreal.load_object(None, cls.get_path_name() + ':' + name + '_GEN_VARIABLE')
    item = {'name': name, 'object': str(c)}
    if isinstance(c, unreal.SceneComponent):
        item['location'] = str(c.get_editor_property('relative_location'))
        item['rotation'] = str(c.get_editor_property('relative_rotation'))
        item['scale'] = str(c.get_editor_property('relative_scale3d'))
    if isinstance(c, unreal.StaticMeshComponent):
        mesh = c.get_editor_property('static_mesh')
        item['mesh'] = str(mesh)
        if mesh:
            item['bounds'] = str(mesh.get_bounds())
    report['components'].append(item)
task = unreal.AssetImportTask()
task.filename = os.path.join(root, 'fbx', 'ImageToStl.com_DJi+Mavic+2+pro+drone+Rail+2020-1.fbx')
task.destination_path = '/Game/Mavic2/Meshes'
task.destination_name = 'SM_Mavic2_Full'
task.automated = True
task.save = True
options = unreal.FbxImportUI()
options.import_mesh = True
options.import_materials = False
options.import_textures = False
options.import_as_skeletal = False
options.automated_import_should_detect_type = False
options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
options.static_mesh_import_data.combine_meshes = True
task.options = options
if not unreal.EditorAssetLibrary.does_asset_exist('/Game/Mavic2/Meshes/SM_Mavic2_Full'):
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
report['imported'] = ['/Game/Mavic2/Meshes/SM_Mavic2_Full']
for path in report['imported']:
    mesh = unreal.load_asset(path)
    report['mavic_bounds'] = str(mesh.get_bounds())
    vertices, triangles, normals, uvs, tangents = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(mesh, 0, 0)
    with open(os.path.join(root, 'artifacts', 'mavic2', 'geometry.json'), 'w') as f:
        json.dump({'vertices': [[v.x, v.y, v.z] for v in vertices], 'triangles': list(triangles)}, f)
os.makedirs(os.path.join(root, 'artifacts', 'mavic2'), exist_ok=True)
with open(os.path.join(root, 'artifacts', 'mavic2', 'inspection.json'), 'w') as f:
    json.dump(report, f, indent=2)
unreal.log('MAVIC2_INSPECTION_COMPLETE ' + json.dumps(report))

