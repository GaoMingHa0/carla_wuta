"""Run in UE4 editor with -ExecCmds=py <this file>."""
import json
import unreal

library = unreal.EditorAssetLibrary
root = '/Game/ChronoTest/'
unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)

def duplicate(source, target):
    if library.does_asset_exist(target):
        return library.load_asset(target)
    asset = library.duplicate_asset(source, target)
    if not asset:
        raise RuntimeError('Cannot duplicate ' + source)
    return asset

factory = duplicate('/Game/Carla/Blueprints/Vehicles/VehicleFactory', root + 'SingleVehicleFactory')
factory_class = library.load_blueprint_class(root + 'SingleVehicleFactory')
cdo = unreal.get_default_object(factory_class)
vehicles = list(cdo.get_editor_property('vehicles'))
chosen = [v for v in vehicles if v.get_editor_property('make').lower() == 'audi'
          and v.get_editor_property('model').lower() == 'tt']
if len(chosen) != 1:
    raise RuntimeError('Expected one Audi TT, found ' + str(len(chosen)))
cdo.set_editor_property('vehicles', chosen)
library.save_loaded_asset(factory, False)

if library.does_asset_exist(root + 'SingleVehicleGameMode'):
    mode = library.load_asset(root + 'SingleVehicleGameMode')
else:
    blueprint_factory = unreal.BlueprintFactory()
    blueprint_factory.set_editor_property('parent_class', unreal.load_class(None, '/Script/Carla.CarlaGameModeBase'))
    mode = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'SingleVehicleGameMode', root.rstrip('/'), unreal.Blueprint, blueprint_factory)
    if not mode:
        raise RuntimeError('Cannot create minimal game mode')
mode_class = library.load_blueprint_class(root + 'SingleVehicleGameMode')
mode_cdo = unreal.get_default_object(mode_class)
weather_path = root + 'MinimalWeather'
if not library.does_asset_exist(weather_path):
    weather_factory = unreal.BlueprintFactory()
    weather_factory.set_editor_property('parent_class', unreal.load_class(None, '/Script/Carla.Weather'))
    weather_asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'MinimalWeather', root.rstrip('/'), unreal.Blueprint, weather_factory)
    library.save_loaded_asset(weather_asset, False)
mode_cdo.set_editor_property('weather_class', library.load_blueprint_class(weather_path))
mode_cdo.set_editor_property('default_pawn_class', unreal.load_class(None, '/Script/Engine.SpectatorPawn'))
mode_cdo.set_editor_property('actor_factories', [
    factory_class, unreal.load_class(None, '/Script/Carla.SensorFactory')])
library.save_loaded_asset(mode, False)

if not unreal.EditorLevelLibrary.load_level(root + 'ChronoFlat'):
    raise RuntimeError('Cannot load ChronoFlat')
world = unreal.EditorLevelLibrary.get_editor_world()
world.get_world_settings().set_editor_property('default_game_mode', mode_class)
for old in unreal.EditorLevelLibrary.get_all_level_actors():
    if old.get_actor_label().startswith('TrackCone_'):
        unreal.EditorLevelLibrary.destroy_actor(old)
for colour, y in [('Red', -400), ('Blue', 400), ('Yellow', 800)]:
    cone_mesh = unreal.load_asset(root + 'Cones/SM_Cone_' + colour)
    if not cone_mesh:
        raise RuntimeError('Missing cone mesh: ' + colour)
    for x in (1500, 2000, 2500, 3000):
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, 0))
        actor.static_mesh_component.set_static_mesh(cone_mesh)
        actor.static_mesh_component.set_collision_profile_name('BlockAll')
        actor.set_actor_label('TrackCone_' + colour + '_' + str(x))
        actor.set_editor_property('tags', ['track_cone', 'cone_' + colour.lower()])
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError('Cannot save ChronoFlat')

summary = {'map': root + 'ChronoFlat', 'game_mode': root + 'SingleVehicleGameMode',
           'factory': root + 'SingleVehicleFactory', 'vehicle': 'vehicle.audi.tt',
           'vehicle_count': len(cdo.get_editor_property('vehicles')),
           'actor_factories': [c.get_path_name() for c in mode_cdo.get_editor_property('actor_factories')]}
with open('/home/wuta/carla/Build/config-logs/single-vehicle-config.json', 'w') as f:
    json.dump(summary, f, indent=2)
unreal.log('SINGLE_VEHICLE_READY: ' + json.dumps(summary))
unreal.SystemLibrary.quit_editor()
