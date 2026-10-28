"""Create a standalone FSACLoop map, keeping the original test map available."""
import json
import os
import unreal

data=json.load(open('/home/wuta/carla/Build/fsac-track/track.json'))
lib=unreal.EditorAssetLibrary
unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
path='/Game/ChronoTest/FSACLoop'
filename='/home/wuta/carla/Unreal/CarlaUE4/Content/ChronoTest/FSACLoop.umap'
if os.path.isfile(filename):
    if not unreal.EditorLevelLibrary.load_level(path):raise RuntimeError('Cannot load map')
elif not unreal.EditorLevelLibrary.new_level_from_template(path,'/Game/ChronoTest/ChronoFlat'):
    raise RuntimeError('Cannot create map from template')

task=unreal.AssetImportTask()
for key,value in [('filename','/home/wuta/carla/Build/fsac-track/FSAC_Road.obj'),
                  ('destination_path','/Game/ChronoTest'),('destination_name','SM_FSACRoad'),
                  ('automated',True),('replace_existing',True),('save',True)]:task.set_editor_property(key,value)
options=unreal.FbxImportUI()
for key,value in [('import_mesh',True),('import_materials',False),('import_textures',False),('import_as_skeletal',False)]:options.set_editor_property(key,value)
options.set_editor_property('mesh_type_to_import',unreal.FBXImportType.FBXIT_STATIC_MESH)
options.static_mesh_import_data.set_editor_property('combine_meshes',True)
options.static_mesh_import_data.set_editor_property('convert_scene',False)
options.static_mesh_import_data.set_editor_property('auto_generate_collision',False)
task.set_editor_property('options',options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
roadmesh=unreal.load_asset('/Game/ChronoTest/SM_FSACRoad')
roadmesh.set_material(0,unreal.load_asset('/Game/ChronoTest/M_ChronoAsphalt'))
lib.save_loaded_asset(roadmesh,False)

apron=unreal.load_asset('/Game/ChronoTest/M_FSACApron')
if not apron:
    apron=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_FSACApron','/Game/ChronoTest',unreal.Material,unreal.MaterialFactoryNew())
    rgb=unreal.MaterialEditingLibrary.create_material_expression(apron,unreal.MaterialExpressionConstant3Vector)
    rgb.set_editor_property('constant',unreal.LinearColor(.18,.2,.18,1))
    unreal.MaterialEditingLibrary.connect_material_property(rgb,'',unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(apron)
    lib.save_loaded_asset(apron,False)

for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    name=actor.get_actor_label()
    if name.startswith(('TrackCone_','FSAC_','ChronoFlat_Spawn_')):
        unreal.EditorLevelLibrary.destroy_actor(actor)
    elif name.startswith('ChronoFlat_Ground'):
        actor.set_actor_location(unreal.Vector(6500,6000,-10),False,False)
        actor.set_actor_scale3d(unreal.Vector(160,140,.2))
        actor.static_mesh_component.set_material(0,apron)

road=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,0,.5))
road.set_actor_label('FSAC_AsphaltRoad_3p5m')
# UE4 OBJ importer reflects Y; undo it to match cone/OpenDRIVE coordinates.
road.set_actor_scale3d(unreal.Vector(1,-1,1))
road.static_mesh_component.set_static_mesh(roadmesh)
road.static_mesh_component.set_collision_profile_name('NoCollision')
meshes={name:unreal.load_asset('/Game/ChronoTest/Cones/SM_Cone_'+name) for name in ('Red','Blue','Yellow')}
for i,cone in enumerate(data['cones']):
    actor=unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(cone['x']*100,cone['y']*100,.5))
    actor.set_actor_label('FSAC_Cone_%s_%03d'%(cone['colour'],i))
    actor.static_mesh_component.set_static_mesh(meshes[cone['colour']])
    actor.static_mesh_component.set_collision_profile_name('BlockAll')
    actor.set_editor_property('tags',['track_cone','cone_'+cone['colour'].lower()])

spawn=data['report']['spawn']
spawnclass=unreal.load_class(None,'/Script/Carla.VehicleSpawnPoint')
actor=unreal.EditorLevelLibrary.spawn_actor_from_class(spawnclass,unreal.Vector(spawn['x']*100,spawn['y']*100,50),unreal.Rotator(0,spawn['yaw_deg'],0))
actor.set_actor_label('FSAC_StartSpawn')
unreal.EditorLevelLibrary.get_editor_world().get_world_settings().set_editor_property('default_game_mode',lib.load_blueprint_class('/Game/ChronoTest/SingleVehicleGameMode'))
if not unreal.EditorLevelLibrary.save_current_level():raise RuntimeError('Cannot save FSACLoop')
unreal.log('FSAC_MAP_READY: '+json.dumps(data['report']))
unreal.SystemLibrary.quit_editor()
