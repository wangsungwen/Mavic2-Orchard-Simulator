"""UE4 commandlet: install split Mavic geometry on existing AirSim rotor components."""
import json
import os
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parts = json.load(open(os.path.join(ROOT, 'fbx/mavic2-separated/parts.json')))
assets = {}
for part in parts:
    name = part['name']
    task = unreal.AssetImportTask()
    task.filename = os.path.join(ROOT, 'fbx/mavic2-separated', name + '.fbx')
    task.destination_path = '/Game/Mavic2/Meshes'
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
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
    data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS
    data.normal_generation_method = unreal.FBXNormalGenerationMethod.BUILT_IN
    data.generate_lightmap_u_vs = False
    data.auto_generate_collision = name.endswith('Body')
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset('/Game/Mavic2/Meshes/' + name)
    assert mesh
    bounds = mesh.get_bounds()
    expected = [(part['max'][i] - part['min'][i])/2 for i in range(3)]
    actual = [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z]
    assert all(abs(a-b)<0.01 for a,b in zip(actual,expected)), (name,actual,expected)
    build = unreal.EditorStaticMeshLibrary.get_lod_build_settings(mesh,0)
    build.use_mikk_t_space = False
    build.generate_lightmap_u_vs = False
    unreal.EditorStaticMeshLibrary.set_lod_build_settings(mesh,0,build)
    assets[name] = mesh

material = unreal.load_asset('/Game/Mavic2/Materials/M_Mavic2_Grey')
prop_mat = unreal.load_asset('/Game/Mavic2/Materials/M_Mavic2_Propeller')
if not prop_mat:
    prop_mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_Mavic2_Propeller','/Game/Mavic2/Materials',unreal.Material,unreal.MaterialFactoryNew())
    color = unreal.MaterialEditingLibrary.create_material_expression(prop_mat,unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant',unreal.LinearColor(0.025,0.03,0.035,1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(prop_mat,unreal.MaterialExpressionConstant)
    rough.set_editor_property('r',0.65)
    unreal.MaterialEditingLibrary.connect_material_property(color,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(prop_mat)
bp = unreal.load_asset('/Game/Mavic2/Blueprints/BP_Mavic2')
cls = unreal.EditorAssetLibrary.load_blueprint_class('/Game/Mavic2/Blueprints/BP_Mavic2')
def comp(name):
    result = unreal.load_object(None,cls.get_path_name()+':'+name+'_GEN_VARIABLE')
    assert result,name
    return result
body = comp('BodyMesh')
body.set_editor_property('static_mesh',assets['SM_Mavic2_Body'])
body.set_editor_property('override_materials',[material])
report = []
for i in range(4):
    part = parts[i]
    prop = comp('Prop'+str(i))
    prop.set_editor_property('static_mesh',assets[part['name']])
    prop.set_editor_property('relative_location',unreal.Vector(*part['pivot_cm']))
    prop.set_editor_property('relative_rotation',unreal.Rotator(0,0,0))
    prop.set_editor_property('relative_scale3d',unreal.Vector(1,1,1))
    prop.set_editor_property('override_materials',[prop_mat])
    prop.set_editor_property('visible',True)
    prop.set_editor_property('hidden_in_game',False)
    prop.set_editor_property('cast_shadow',True)
    prop.set_editor_property('cast_hidden_shadow',False)
    prop.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    rotation = comp('Rotation'+str(i))
    # Existing BP BeginPlay wires these components; retain that graph and the
    # native FlyingPawn motor-speed callbacks. Set template association too.
    rotation.set_updated_component(prop)
    report.append({'rotor':i,'mesh':prop.static_mesh.get_path_name(),'pivot':part['pivot_cm'],
                   'rotation_component':rotation.get_path_name()})
for name,mesh in assets.items():
    mesh.set_material(0, material if name.endswith('Body') else prop_mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_loaded_asset(prop_mat,only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_loaded_asset(bp,only_if_is_dirty=False)
json.dump(report,open(os.path.join(ROOT,'artifacts/mavic2/rotor-import.json'),'w'),indent=2)
unreal.log('MAVIC2_ROTORS_IMPORTED '+json.dumps(report))
