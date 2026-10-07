#!/usr/bin/env bash
# Rebuild every map and the character models with Blender.
set -euo pipefail
cd "$(dirname "$0")/.."
BLENDER="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"
for script in blender/characters.py blender/maps/*.py; do
  [ -f "$script" ] || continue
  echo "== $script"
  "$BLENDER" -b --factory-startup -P "$script" -- "$@" 2>&1 | grep -E "^\[gh\]|^\[chars\]|Error|Traceback" || true
done
for json in shared/maps/*.json; do
  node scripts/check-map.mjs "$(basename "$json" .json)" | tail -1
done
