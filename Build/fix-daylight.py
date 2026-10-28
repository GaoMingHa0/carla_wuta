import json
import unreal

unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
lib=unreal.EditorAssetLibrary
sky_material=unreal.load_asset('/Game/ChronoTest/M_DaylightSky')
if not sky_material:
    sky_material=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_DaylightSky','/Game/ChronoTest',unreal.Material,unreal.MaterialFactoryNew())
    sky_material.set_editor_property('two_sided',True)
    sky_material.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT)
    rgb=unreal.MaterialEditingLibrary.create_material_expression(sky_material,unreal.MaterialExpressionConstant3Vector)
    rgb.set_editor_property('constant',unreal.LinearColor(.32,.55,.85,1))
    assert unreal.MaterialEditingLibrary.connect_material_property(rgb,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(sky_material)
    lib.save_loaded_asset(sky_material,False)

def spawn(cls, label, location):
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(cls,location)
    actor.set_actor_label(label)
    return actor

report={}
for mapname in ['ChronoFlat','FSACLoop']:
    if not unreal.EditorLevelLibrary.load_level('/Game/ChronoTest/'+mapname):raise RuntimeError('Load failed')
    for actor in unreal.EditorLevelLibrary.get_all_level_actors():
        if actor.get_actor_label().startswith('Daylight_'):
            unreal.EditorLevelLibrary.destroy_actor(actor)
        elif actor.get_actor_label()=='ChronoFlat_Sun':
            actor.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            actor.light_component.set_editor_property('intensity',5.0)
            actor.set_actor_rotation(unreal.Rotator(-55,-30,0),False)
    sky=spawn(unreal.StaticMeshActor,'Daylight_SkyDome',unreal.Vector(6500,6000,0))
    sky.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Sphere.Sphere'))
    sky.static_mesh_component.set_material(0,sky_material)
    sky.static_mesh_component.set_collision_profile_name('NoCollision')
    sky.static_mesh_component.set_editor_property('cast_shadow',False)
    sky.set_actor_scale3d(unreal.Vector(1000,1000,1000))
    light=spawn(unreal.SkyLight,'Daylight_Ambient',unreal.Vector(6500,6000,1000))
    comp=light.get_component_by_class(unreal.SkyLightComponent)
    comp.set_mobility(unreal.ComponentMobility.MOVABLE)
    comp.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    comp.set_editor_property('cubemap',unreal.load_asset('/Engine/EngineResources/GrayTextureCube.GrayTextureCube'))
    comp.set_editor_property('intensity',1.5)
    comp.set_editor_property('lower_hemisphere_is_black',False)
    pp=spawn(unreal.PostProcessVolume,'Daylight_Exposure',unreal.Vector(0,0,0))
    pp.set_editor_property('unbound',True)
    settings=pp.get_editor_property('settings')
    for prop,value in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),
                       ('auto_exposure_min_brightness',1.0),('auto_exposure_max_brightness',1.0),
                       ('override_auto_exposure_bias',True),('auto_exposure_bias',0.0),
                       ('override_auto_exposure_apply_physical_camera_exposure',True),('auto_exposure_apply_physical_camera_exposure',False)]:
        settings.set_editor_property(prop,value)
    pp.set_editor_property('settings',settings)
    if not unreal.EditorLevelLibrary.save_current_level():raise RuntimeError('Save failed')
    report[mapname]={'sky':'blue unlit dome','ambient_intensity':1.5,'sun_intensity':5,'fixed_exposure':1.0}
open('/home/wuta/carla/Build/config-logs/daylight-config.json','w').write(json.dumps(report,indent=2))
unreal.log('DAYLIGHT_READY: '+str(report))
unreal.SystemLibrary.quit_editor()
