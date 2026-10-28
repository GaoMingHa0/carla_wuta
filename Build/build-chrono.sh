#!/usr/bin/env bash
set -eo pipefail
source /home/wuta/miniforge3/etc/profile.d/conda.sh
conda activate carla
cd /home/wuta/carla
# Conda Python's default GCC flags are incompatible with UE4's Clang 10.
export CFLAGS='-O2 -fPIC'
export CXXFLAGS='-O2 -fPIC'
make setup ARGS='--chrono'
bash Util/BuildTools/BuildLibCarla.sh --client --server --release
bash Util/BuildTools/BuildOSM2ODR.sh --build
bash Util/BuildTools/BuildPythonAPI.sh --rebuild
bash Util/BuildTools/BuildCarlaUE4.sh --build --chrono --no-simready
