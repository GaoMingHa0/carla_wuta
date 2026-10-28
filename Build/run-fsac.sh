#!/usr/bin/env bash
set -e
export CARLA_MAP=/Game/ChronoTest/FSACLoop
export CARLA_VISIBLE=${CARLA_VISIBLE:-1}
exec bash /home/wuta/carla/Build/run-chrono.sh "$@"
