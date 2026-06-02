#! /bin/bash
# ===========================================================================
# download_from_hex.sh — Download rendered images from Hex to your Mac
#
# Usage:
#   ./scripts/download_from_hex.sh <remote_name> [local_output_dir]
#
# Examples:
#   ./scripts/download_from_hex.sh lego
#   ./scripts/download_from_hex.sh lego ./output/lego_renders
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

REMOTE_NAME="${1:?Usage: download_from_hex.sh <remote_name> [local_output_dir]}"
LOCAL_DIR="${2:-${REPO_DIR}/output/${REMOTE_NAME}}"
REMOTE_PATH="${HEX_WORK_DIR}/${REMOTE_NAME}/gsplat_renders"

echo "=== Downloading renders from Hex ==="
echo "  Remote: ${HEX_USER}@${HEX_NODE}:${REMOTE_PATH}"
echo "  Local:  ${LOCAL_DIR}"
echo ""

mkdir -p "${LOCAL_DIR}"

rsync -avz --progress \
    "${HEX_USER}@${HEX_NODE}:${REMOTE_PATH}/" \
    "${LOCAL_DIR}/"

echo ""
echo "=== Done! $(ls "${LOCAL_DIR}" | wc -l | tr -d ' ') images downloaded to ${LOCAL_DIR} ==="
