# CARLA 0.9.16 + Chrono local check

Use the Conda `carla` environment. The launcher activates it automatically.

```bash
cd /home/wuta/carla
# Physics only; no camera rendering, no Town01
CARLA_PHYSICS_ONLY=1 bash Build/run-chrono.sh
# Or render the minimal map with NVIDIA
bash Build/run-chrono.sh
```

Run the short check in a second terminal:

```bash
source /home/wuta/miniforge3/etc/profile.d/conda.sh
conda activate carla
python /home/wuta/carla/Build/chrono-smoke.py
```

Stop the instance:

```bash
bash /home/wuta/carla/Build/stop-chrono.sh
```

RPC/streaming/secondary ports: 2200/2201/2202.

Map: `/Game/ChronoTest/ChronoFlat`; 300 m × 40 m plane,
one registered vehicle (`vehicle.audi.tt`), collision sensor support,
four red, four blue and four yellow cones.
The cone white band spans 6–14 cm measured downward along the conical side from its top.
Cone dimensions are 20 × 20 × 28 cm. The STEP side length is approximately 26.68 cm.

Recorded acceptance: official Chrono sedan templates, 0.02 s synchronous ticks,
4 s controlled simulation, 2.4068 m displacement, 1.3277 m/s maximum speed,
0 m/s final speed, no collision callbacks. Server log confirms Chrono template
loading and no PhysX fallback during this short check.

Evidence: `Build/config-logs/chrono-smoke-result.json`, `chrono-final-smoke.log`,
`runtime-scene-check.json`, and `runtime-final-scene.log` (or the project Saved log).

This verifies a short physics integration check. WUTA vehicle dynamics,
ROS 2/MPC integration, camera rendering of cone materials, retroreflection,
and long-run stability have not yet been accepted.
