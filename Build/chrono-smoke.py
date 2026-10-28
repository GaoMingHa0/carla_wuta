"""Short movement check using CARLA's official Chrono sedan templates."""
import json
import math
import os
import time
from pathlib import Path

import carla

root = Path('/home/wuta/carla')
port = int(os.environ.get('CARLA_RPC_PORT', '2200'))
client = carla.Client('127.0.0.1', port)
client.set_timeout(10.0)
world = None
deadline = time.monotonic() + 600
while world is None:
    try:
        world = client.get_world()
    except RuntimeError:
        if time.monotonic() > deadline:
            raise
        time.sleep(2)

print('Connected', flush=True)
original = world.get_settings()
vehicle = None
sensor = None
collisions = []
samples = []
try:
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = 0.02
    settings.no_rendering_mode = True
    print('Applying synchronous settings', flush=True)
    world.apply_settings(settings)
    print('Settings applied', flush=True)
    print('Fetching vehicle blueprint', flush=True)
    bp = world.get_blueprint_library().find('vehicle.audi.tt')
    bp.set_attribute('role_name', 'chrono_smoke')
    print('Fetching spawn points', flush=True)
    for spawn in world.get_map().get_spawn_points():
        print('Spawning at', spawn, flush=True)
        vehicle = world.try_spawn_actor(bp, spawn)
        if vehicle is not None:
            break
    if vehicle is None:
        raise RuntimeError('No free spawn point')
    print('Vehicle spawned', vehicle.id, flush=True)
    sensor = world.spawn_actor(world.get_blueprint_library().find('sensor.other.collision'),
                               carla.Transform(), attach_to=vehicle)
    sensor.listen(lambda event: collisions.append({'frame': event.frame,
                                                  'other': event.other_actor.type_id}))
    for _ in range(50):
        world.tick()
    collisions.clear()
    print('Enabling Chrono', flush=True)
    vehicle.enable_chrono_physics(
        5000, 0.002, 'sedan/vehicle/Sedan_Vehicle.json',
        'sedan/powertrain/Sedan_SimpleMapPowertrain.json',
        'sedan/tire/Sedan_TMeasyTire.json',
        str(root / 'Co-Simulation/Chrono/Vehicles') + '/')
    for _ in range(50):
        world.tick()
    print('Chrono settled; starting control', flush=True)
    start = vehicle.get_location()
    for i in range(200):
        vehicle.apply_control(carla.VehicleControl(throttle=0.35 if i < 150 else 0.0,
                                                   brake=0.0 if i < 150 else 1.0))
        frame = world.tick()
        p = vehicle.get_location()
        v = vehicle.get_velocity()
        samples.append({'frame': frame, 'x': p.x, 'y': p.y, 'z': p.z,
                        'speed_mps': math.sqrt(v.x*v.x + v.y*v.y + v.z*v.z)})
    end = vehicle.get_location()
    displacement = math.hypot(end.x - start.x, end.y - start.y)
    maximum_speed = max(s['speed_mps'] for s in samples)
    result = {'server_version': client.get_server_version(), 'rpc_port': port, 'map': world.get_map().name,
              'vehicle': vehicle.type_id, 'fixed_delta_seconds': 0.02,
              'controlled_sim_seconds': 4.0, 'displacement_m': displacement,
              'max_speed_mps': maximum_speed, 'final_speed_mps': samples[-1]['speed_mps'],
              'collisions': collisions, 'samples': samples,
              'movement_check_pass': displacement > 0.5 and maximum_speed > 0.5 and not collisions,
              'note': 'Check server log for Chrono template loading and absence of PhysX fallback.'}
    output = root / 'Build/config-logs/chrono-smoke-result.json'
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'samples'}, indent=2), flush=True)
    if not result['movement_check_pass']:
        raise RuntimeError('Movement check failed; inspect result and server log')
finally:
    if sensor is not None:
        sensor.stop()
        sensor.destroy()
    if vehicle is not None:
        vehicle.destroy()
    world.apply_settings(original)
