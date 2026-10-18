"""Import the supplied FBX and build an independent AirSim pawn in UE4.27.

Run using UE4Editor-Cmd -run=pythonscript with PythonScriptPlugin and
EditorScriptingUtilities enabled. Scale is a visual approximation, not a
calibration of DJI geometry or flight dynamics. If split rotor sources exist,
the rotor importer is run last to preserve motor-driven propellers.
"""
import json
import os
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MESH_PATH = '/Game/Mavic2/Meshes/SM_Mavic2_Full'
BP_PATH = '/Game/Mavic2/Blueprints/BP_Mavic2'

task = unreal.AssetImportTask()
task.filename = os.path.join(ROOT, 'fbx', 'ImageToStl.com_DJi+Mavic+2+pro+drone+Rail+2020-1.fbx')
task.destination_path = '/Game/Mavic2/Meshes'
task.destination_name = 'SM_Mavic2_Full'
task.automated = True
task.replace_existing = True
task.replace_existing_settings = True
task.save = True
options = unreal.FbxImportUI()
options.import_mesh = True
options.import_materials = False
options.import_textures = False
options.import_as_skeletal = False
options.automated_import_should_detect_type = False
options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
data = options.static_mesh_import_data
data.combine_meshes = True
data.import_uniform_scale = 8.0
data.import_rotation = unreal.Rotator(pitch=0, yaw=-90, roll=90)
data.import_translation = unreal.Vector(-20.89932, 23.43496, -7.707744)
data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS
data.normal_generation_method = unreal.FBXNormalGenerationMethod.BUILT_IN
data.generate_lightmap_u_vs = False
existing_mesh = unreal.load_asset(MESH_PATH)
if existing_mesh:
    stored = existing_mesh.get_editor_property('asset_import_data')
    for name in ['import_uniform_scale', 'import_rotation', 'import_translation',
                 'normal_import_method', 'normal_generation_method', 'generate_lightmap_u_vs']:
        stored.set_editor_property(name, data.get_editor_property(name))
task.options = options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
mesh = unreal.load_asset(MESH_PATH)
assert mesh, 'Mesh import failed'
build = unreal.EditorStaticMeshLibrary.get_lod_build_settings(mesh, 0)
build.use_mikk_t_space = False
build.recompute_normals = True
build.recompute_tangents = True
build.generate_lightmap_u_vs = False
unreal.EditorStaticMeshLibrary.set_lod_build_settings(mesh, 0, build)

mat_path = '/Game/Mavic2/Materials/M_Mavic2_Grey'
material = unreal.load_asset(mat_path)
if material is None:
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'M_Mavic2_Grey', '/Game/Mavic2/Materials', unreal.Material, unreal.MaterialFactoryNew())
    color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant', unreal.LinearColor(0.18, 0.20, 0.23, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
    rough.set_editor_property('r', 0.65)
    unreal.MaterialEditingLibrary.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
mesh.set_material(0, material)

bp = unreal.load_asset(BP_PATH)
if bp is None:
    source_bp = unreal.load_asset('/AirSim/Blueprints/BP_FlyingPawn')
    bp = unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('BP_Mavic2', '/Game/Mavic2/Blueprints', source_bp)
assert bp, 'Blueprint duplication failed'
cls = unreal.EditorAssetLibrary.load_blueprint_class(BP_PATH)

def component(name):
    obj = unreal.load_object(None, cls.get_path_name() + ':' + name + '_GEN_VARIABLE')
    assert obj, 'Missing component: ' + name
    return obj

body = component('BodyMesh')
body.set_editor_property('static_mesh', mesh)
body.set_editor_property('override_materials', [material])
body.set_editor_property('relative_scale3d', unreal.Vector(1, 1, 1))
for i in range(4):
    prop = component('Prop' + str(i))
    prop.set_editor_property('visible', False)
    prop.set_editor_property('hidden_in_game', True)
    prop.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)

# Coordinates in centimeters, just outside the camera housing / body surface.
for name, location in {
    'FrontCenterCamera': (12, 0, -1),
    'FrontLeftCamera': (12, -3, -1),
    'FrontRightCamera': (12, 3, -1),
    'BackCenterCamera': (-12, 0, 0),
    'BottomCenterCamera': (0, 0, -6),
}.items():
    component(name).set_editor_property('relative_location', unreal.Vector(*location))

if hasattr(unreal, 'BlueprintEditorLibrary'):
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
for asset in [material, mesh, bp]:
    assert unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
report = {'mesh': mesh.get_path_name(), 'blueprint': bp.get_path_name(),
          'bounds': str(mesh.get_bounds()), 'visual_scale': 8.0,
          'propellers': 'static geometry; original animated props hidden',
          'physics': 'unchanged SimpleFlight', 'material': material.get_path_name()}
with open(os.path.join(ROOT, 'artifacts', 'mavic2', 'import-result.json'), 'w') as f:
    json.dump(report, f, indent=2)
unreal.log('MAVIC2_IMPORT_COMPLETE ' + json.dumps(report))
if os.path.isfile(os.path.join(ROOT, 'fbx/mavic2-separated/parts.json')):
    import runpy
    runpy.run_path(os.path.join(ROOT, 'scripts/Import-Mavic2-Rotors.py'))
    report['mesh'] = '/Game/Mavic2/Meshes/SM_Mavic2_Body'
    report['propellers'] = 'four separate meshes driven by AirSim motor speeds'
    with open(os.path.join(ROOT, 'artifacts/mavic2/import-result.json'), 'w') as f:
        json.dump(report, f, indent=2)
