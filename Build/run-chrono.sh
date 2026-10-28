#!/usr/bin/env bash
set -eo pipefail
source /home/wuta/miniforge3/etc/profile.d/conda.sh
conda activate carla
export __NV_PRIME_RENDER_OFFLOAD=1
export __GLX_VENDOR_LIBRARY_NAME=nvidia
export __VK_LAYER_NV_optimus=NVIDIA_only
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json
export VK_DRIVER_FILES="$VK_ICD_FILENAMES"
export LD_LIBRARY_PATH="/home/wuta/carla/Unreal/CarlaUE4/Plugins/Carla/CarlaDependencies/lib:${LD_LIBRARY_PATH:-}"
if ss -ltnH 'sport = :2200' | rg -q .; then
  echo 'Port 2200 is already in use'; exit 1
fi
render_args=(-RenderOffScreen)
if [ "${CARLA_PHYSICS_ONLY:-0}" = 1 ]; then
  render_args=(-nullrhi)
elif [ "${CARLA_VISIBLE:-0}" = 1 ]; then
  render_args=(-windowed -ResX=1280 -ResY=720)
fi
exec "$UE4_ROOT/Engine/Binaries/Linux/UE4Editor" \
  "$CARLA_UE4_ROOT/Unreal/CarlaUE4/CarlaUE4.uproject" \
  "${CARLA_MAP:-/Game/ChronoTest/ChronoFlat}" -game "${render_args[@]}" -nosound -unattended \
  -carla-rpc-port=2200 -carla-streaming-port=2201 -carla-secondary-port=2202 \
  -quality-level=Low -log "$@"
