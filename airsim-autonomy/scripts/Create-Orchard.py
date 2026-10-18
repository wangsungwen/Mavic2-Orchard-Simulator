"""UE4.27 editor Python: generate a separate, reproducible synthetic orchard map."""
import json
import os
import unreal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'artifacts', 'orchard')
os.makedirs(OUT, exist_ok=True)
MAP = '/Game/Orchard/Maps/Orchard_Hillside'
COLORS = {
    'Ground': (0.18, 0.23, 0.075), 'Bark': (0.10, 0.055, 0.025),
    'Leaves': (0.055, 0.23, 0.025), 'Orange': (1.0, 0.29, 0.008),
    'Shrub': (0.16, 0.30, 0.055), 'Track': (0.36, 0.25, 0.13),
    'Pad': (0.25, 0.29, 0.30), 'Fur': (0.29, 0.22, 0.13),
    'Face': (0.65, 0.36, 0.28),
}
for name, rgb in COLORS.items():
    path = '/Game/Orchard/Materials/M_' + name
    material = unreal.load_asset(path)
    if not material:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            'M_' + name, '/Game/Orchard/Materials', unreal.Material, unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.delete_all_material_expressions(material)
    material.set_editor_property('used_with_instanced_static_meshes', True)
    color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant3Vector)
    color.set_editor_property('constant', unreal.LinearColor(*rgb, 1))
    unreal.MaterialEditingLibrary.connect_material_property(color, '', unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant)
    rough.set_editor_property('r', 0.85)
    unreal.MaterialEditingLibrary.connect_material_property(rough, '', unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)

if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    assert unreal.EditorLevelLibrary.load_level(MAP)
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if not isinstance(actor, (unreal.WorldSettings, unreal.LevelScriptActor)):
            actor.set_actor_label('Replaced_' + actor.get_name())
            unreal.EditorLevelLibrary.destroy_actor(actor)
else:
    assert unreal.EditorLevelLibrary.new_level(MAP), 'Could not create orchard level'
world = unreal.EditorLevelLibrary.get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', unreal.load_class(None, '/Script/AirSim.AirSimGameMode'))

def spawn(cls, label, xyz, rotation=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(cls, unreal.Vector(*xyz), rotation or unreal.Rotator())
    assert actor, label
    actor.set_actor_label(label)
    actor.set_editor_property('tags', [unreal.Name(label)])
    return actor

scene = spawn(unreal.load_class(None, '/Script/Blocks.OrchardScene'), 'Orchard_Synthetic_100m', (0, 0, 0))
spawn(unreal.PlayerStart, 'Orchard_Home', (-3600, 0, 45))
sun = spawn(unreal.DirectionalLight, 'Orchard_Sun', (0, 0, 5000), unreal.Rotator(-38, -35, 0))
sun.light_component.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
sun.light_component.set_editor_property('intensity', 3.0)
sky = spawn(unreal.SkyLight, 'Orchard_SkyLight', (0, 0, 2500))
sky.light_component.set_editor_property('mobility', unreal.ComponentMobility.MOVABLE)
sky.light_component.set_editor_property('intensity', 1.0)
sky_class = unreal.EditorAssetLibrary.load_blueprint_class('/Engine/EngineSky/BP_Sky_Sphere')
if sky_class:
    sky_actor = spawn(sky_class, 'Orchard_Sky', (0, 0, 0))
    # Keep the engine sky's default daylight palette; sunlight is fixed in v1.
spawn(unreal.ExponentialHeightFog, 'Orchard_Haze', (0, 0, -500))

positions = [(-1250, -1350), (-350, 1350), (1400, -2250), (2300, 2250)]
for i, (x, y) in enumerate(positions):
    actor = spawn(unreal.load_class(None, '/Script/Blocks.OrchardMacaque'), 'Macaque_%02d' % (i+1), (x, y, 100))
    actor.set_editor_property('individual', i)

unreal.EditorLevelLibrary.set_level_viewport_camera_info(unreal.Vector(-6100, -7000, 5800), unreal.Rotator(-30, 48, 0))
assert unreal.EditorLevelLibrary.save_current_level(), 'Map save failed'
report = {'map': MAP, 'synthetic': True, 'area_m': [100, 100], 'trees': 64,
          'macaques': 4, 'seed': 20261018, 'home_ue_cm': [-3600, 0, 45],
          'limitations': ['primitive proxy vegetation and animals', 'scripted movement, not animal behavior model',
                           'no climbing, detector or avoidance', 'not surveyed or georeferenced']}
with open(os.path.join(OUT, 'scene-build.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2)
unreal.log('ORCHARD_BUILD_COMPLETE ' + json.dumps(report))
