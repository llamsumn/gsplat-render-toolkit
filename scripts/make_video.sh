#! /bin/bash
# ===========================================================================
# make_video.sh — Turn rendered frames into an MP4 video
#
# Requires: ffmpeg (install with: brew install ffmpeg)
#
# Usage:
#   ./scripts/make_video.sh /path/to/renders [output.mp4] [fps]
#
# Examples:
#   ./scripts/make_video.sh ./output/lego
#   ./scripts/make_video.sh ./output/lego lego_turntable.mp4 30
# ===========================================================================

set -euo pipefail

FRAMES_DIR="${1:?Usage: make_video.sh /path/to/renders [output.mp4] [fps]}"
OUTPUT="${2:-${FRAMES_DIR}/video.mp4}"
FPS="${3:-30}"

# Check ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ERROR: ffmpeg not found. Install with: brew install ffmpeg"
    exit 1
fi

NUM_FRAMES=$(ls "${FRAMES_DIR}"/*.png 2>/dev/null | wc -l | tr -d ' ')
echo "=== Creating video ==="
echo "  Frames: ${NUM_FRAMES} PNGs in ${FRAMES_DIR}"
echo "  Output: ${OUTPUT}"
echo "  FPS:    ${FPS}"
echo ""

ffmpeg -y \
    -framerate "${FPS}" \
    -pattern_type glob \
    -i "${FRAMES_DIR}/*.png" \
    -c:v libx264 \
    -pix_fmt yuv420p \
    -crf 18 \
    "${OUTPUT}"

echo ""
echo "=== Done! Video saved to ${OUTPUT} ==="
echo "  Duration: $(echo "scale=1; ${NUM_FRAMES} / ${FPS}" | bc)s at ${FPS} fps"
