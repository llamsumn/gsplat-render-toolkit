#! /bin/bash
# ===========================================================================
# run_hex.sh — Render a 3DGS scene on Hex using gsplat
#
# Usage (on Hex):
#   cd /mnt/fast0/clll20/my_scene
#   bash ~/gsplat-render-toolkit/run_hex.sh \
#       --ply point_cloud/iteration_30000/point_cloud.ply \
#       --cameras cameras.json \
#       --output ./gsplat_renders
#
# Or with defaults (looks for standard 3DGS paths in current directory):
#   bash ~/gsplat-render-toolkit/run_hex.sh
#
# The render runs in the background via nohup. Check progress with:
#   tail -f render_log.txt
# ===========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RENDER_SCRIPT="${SCRIPT_DIR}/render_gsplat.py"
LOG_FILE="render_log.txt"

# Activate the venv
if [ -d "${HOME}/gsplat_env" ]; then
    source "${HOME}/gsplat_env/bin/activate"
else
    echo "ERROR: gsplat_env not found. Run setup_hex.sh first."
    exit 1
fi

echo "=== Starting render (background, logging to ${LOG_FILE}) ==="
echo "    Script: ${RENDER_SCRIPT}"
echo "    Args:   $*"
echo ""

nohup python3 "${RENDER_SCRIPT}" "$@" 1> "${LOG_FILE}" 2>&1 &
RENDER_PID=$!

echo "Render started (PID: ${RENDER_PID})"
echo "Safe to disconnect. Monitor with: tail -f ${LOG_FILE}"
echo ""

# Show the first few lines so you can see it started
sleep 3
tail -10 "${LOG_FILE}"
