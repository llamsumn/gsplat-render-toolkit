#! /bin/bash
# ===========================================================================
# upload_to_hex.sh — Upload a 3DGS scene from your Mac to Hex
#
# Usage:
#   ./scripts/upload_to_hex.sh /path/to/local/scene [remote_name]
#
# Examples:
#   ./scripts/upload_to_hex.sh ./examples/lego
#   ./scripts/upload_to_hex.sh /Users/kahncant/gaussian-splatting-results/lego my_lego
# ===========================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "${SCRIPT_DIR}")"

# Load .env if it exists
if [ -f "${REPO_DIR}/.env" ]; then
    source "${REPO_DIR}/.env"
fi

HEX_USER="${HEX_USER:?Set HEX_USER in .env}"
HEX_NODE="${HEX_NODE:?Set HEX_NODE in .env}"
HEX_WORK_DIR="${HEX_WORK_DIR:-/mnt/fast0/${HEX_USER}/gsplat_work}"

LOCAL_PATH="${1:?Usage: upload_to_hex.sh /path/to/scene [remote_name]}"
REMOTE_NAME="${2:-$(basename "${LOCAL_PATH}")}"
REMOTE_PATH="${HEX_WORK_DIR}/${REMOTE_NAME}"

echo "=== Uploading to Hex ==="
echo "  Local:  ${LOCAL_PATH}"
echo "  Remote: ${HEX_USER}@${HEX_NODE}:${REMOTE_PATH}"
echo ""

# Create remote directory
ssh "${HEX_USER}@${HEX_NODE}" "mkdir -p '${REMOTE_PATH}'"

# Upload — only the files gsplat needs (skip full render outputs)
rsync -avz --progress \
    --include='cameras.json' \
    --include='cfg_args' \
    --include='point_cloud/***' \
    --exclude='gsplat_renders/' \
    --exclude='test/' \
    --exclude='train/' \
    --exclude='*.log' \
    "${LOCAL_PATH}/" \
    "${HEX_USER}@${HEX_NODE}:${REMOTE_PATH}/"

# Also upload the render script
rsync -avz "${REPO_DIR}/render_gsplat.py" "${HEX_USER}@${HEX_NODE}:${REMOTE_PATH}/render_gsplat.py"

echo ""
echo "=== Done! Now SSH in and run: ==="
echo "  ssh ${HEX_USER}@${HEX_NODE}"
echo "  cd ${REMOTE_PATH}"
echo "  bash ~/gsplat-render-toolkit/run_hex.sh"
