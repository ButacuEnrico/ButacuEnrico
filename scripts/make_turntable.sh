#!/bin/zsh
# Render the turntable frames in Blender and pack them into turntable.webp.
#   scripts/make_turntable.sh [samples] [percent] [out.webp]
# Not part of update.sh: a full render takes several minutes.
# Frames stay in build/frames (git-ignored) so the WebP can be re-packed alone.
set -euo pipefail
cd "$(dirname "$0")/.."
SAMPLES=${1:-32}
PERCENT=${2:-100}
OUT=${3:-turntable.webp}
FRAMES=build/frames
rm -rf "$FRAMES" && mkdir -p "$FRAMES"
/Applications/Blender.app/Contents/MacOS/Blender -b -P scripts/turntable.py -- "$PWD/$FRAMES" 1 96 "$SAMPLES" "$PERCENT" | grep -E "^frame 96|Error" || true
# -kmax 1 makes every frame a full key frame (-kmax 0 does not): no blended
# transparent sub-frames, which smear lossy animations into ghost stripes
# 42 ms per frame is about 24 fps
img2webp -loop 0 -kmax 1 -sharp_yuv -lossy -q 80 -m 6 -exact -d 42 "$FRAMES"/f*.png -o "$OUT"
ls -la "$OUT"
