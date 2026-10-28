#!/usr/bin/env bash
set -euo pipefail
root=/home/wuta/carla
exec 9>"$root/Build/content.lock"
flock -n 9 || { echo 'Content preparation already running'; exit 1; }
trap 'rc=$?; if [ "$rc" -ne 0 ]; then echo "FAILED (exit $rc), rerun: bash $root/Build/prepare-content.sh"; fi' EXIT
target="$root/Unreal/CarlaUE4/Content/Carla"
version=20250912_2171890
if [ -f "$target/.version" ] && [ "$(cat "$target/.version")" = "$version" ]; then
  echo 'Content already ready'; exit 0
fi
if [ -e "$target" ]; then
  echo "Refusing to overwrite existing $target"; exit 1
fi
aria2c --continue=true --auto-file-renaming=false --allow-overwrite=false \
  --file-allocation=none --max-connection-per-server=16 --split=16 \
  --min-split-size=32M --summary-interval=60 --show-console-readout=false \
  --console-log-level=notice --dir="$root" --out=Content.tar.gz \
  "https://carla-assets.s3.us-east-005.backblazeb2.com/$version.tar.gz"
echo 'Download complete; extracting content'
staging="$root/Build/content-staging"
mkdir -p "$staging"
tar -xzf "$root/Content.tar.gz" -C "$staging"
printf '%s\n' "$version" > "$staging/.version"
mkdir -p "$(dirname "$target")"
mv "$staging" "$target"
echo "READY: $target ($version)"
