#!/bin/zsh
# Render the turntable frames in Blender and pack them into turntable.webp.
#   scripts/make_turntable.sh [samples] [percent] [out.webp]
# Not part of update.sh: a full render takes tens of minutes.
set -euo pipefail
cd "$(dirname "$0")/.."
SAMPLES=${1:-32}
PERCENT=${2:-100}
OUT=${3:-turntable.webp}
FRAMES=$(mktemp -d)
/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/turntable.py -- "$FRAMES" 1 96 "$SAMPLES" "$PERCENT" | grep -E "^frame|Error"
# 42 ms per frame is about 24 fps; -mixed picks lossy or lossless per frame
img2webp -loop 0 -mixed -q 72 -d 42 "$FRAMES"/f*.png -o "$OUT"
rm -rf "$FRAMES"
ls -la "$OUT"
