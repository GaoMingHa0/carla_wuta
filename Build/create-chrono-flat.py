"""Run inside UE4's PythonScript commandlet to create a minimal test map."""
import unreal
import os

path = '/Game/ChronoTest/ChronoFlat'
create = unreal.EditorLevelLibrary.load_level if os.path.isfile('/home/wuta/carla/Unreal/CarlaUE4/Content/ChronoTest/ChronoFlat.umap') else unreal.EditorLevelLibrary.new_level
if not create(path):
    raise RuntimeError('Cannot create ' + path)
def spawn_actor(actor_class, location, rotation=unreal.Rotator(0, 0, 0)):
    return unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)

for old in unreal.EditorLevelLibrary.get_all_level_actors():
    if old.get_actor_label().startswith('ChronoFlat_'):
        unreal.EditorLevelLibrary.destroy_actor(old)

ground = spawn_actor(
    unreal.StaticMeshActor, unreal.Vector(15000, 0, -10))
ground.set_actor_label('ChronoFlat_Ground_300m_x_40m')
ground.static_mesh_component.set_static_mesh(unreal.load_asset('/Engine/BasicShapes/Cube.Cube'))
ground.set_actor_scale3d(unreal.Vector(300, 40, 0.2))
ground.static_mesh_component.set_collision_profile_name('BlockAll')

light = spawn_actor(
    unreal.DirectionalLight, unreal.Vector(15000, 0, 1000), unreal.Rotator(-55, -30, 0))
light.set_actor_label('ChronoFlat_Sun')
light.light_component.set_editor_property('intensity', 3.0)
light.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)

spawn_class = unreal.load_class(None, '/Script/Carla.VehicleSpawnPoint')
for x in (1000, 5000, 10000):
    spawn = spawn_actor(
        spawn_class, unreal.Vector(x, 175, 50), unreal.Rotator(0, 0, 0))
    spawn.set_actor_label('ChronoFlat_Spawn_' + str(x))

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError('Cannot save ' + path)
unreal.log('CHRONO_FLAT_READY: ' + path)
unreal.SystemLibrary.quit_editor()
