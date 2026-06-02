#! /bin/bash
# ===========================================================================
# setup_hex.sh — Run ONCE on a Hex node to create the Python environment
#
# The venv and JIT cache live on /mnt/fast0/ to avoid the 25GB home quota.
#
# Usage:
#   ssh YOUR_USER@YOUR_NODE
#   bash ~/gsplat-render-toolkit/setup_hex.sh
# ===========================================================================

set -euo pipefail

HEX_USER="$(whoami)"
VENV_DIR="/mnt/fast0/${HEX_USER}/gsplat_env"
TORCH_EXT_DIR="/mnt/fast0/${HEX_USER}/torch_extensions"

echo "=== Creating virtual environment at ${VENV_DIR} ==="
mkdir -p "$(dirname "${VENV_DIR}")"
python3 -m venv "${VENV_DIR}"
source "${VENV_DIR}/bin/activate"

echo "=== Installing PyTorch 2.5.1 (CUDA 12.1) ==="
pip install --upgrade pip
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121

echo "=== Installing gsplat from source (compiles CUDA kernels — ~5-10 min) ==="
export TORCH_EXTENSIONS_DIR="${TORCH_EXT_DIR}"
mkdir -p "${TORCH_EXT_DIR}"
pip install --no-build-isolation git+https://github.com/nerfstudio-project/gsplat.git@v1.5.0

echo "=== Installing remaining dependencies ==="
pip install plyfile Pillow packaging

echo ""
echo "=== Verifying installation ==="
python3 -c "import torch; print('CUDA:', torch.cuda.is_available(), torch.cuda.get_device_name(0))"
python3 -c "from gsplat import csrc; print('gsplat OK (pre-compiled CUDA kernels)')"

echo ""
echo "=== Done! ==="
echo "Activate with:  source ${VENV_DIR}/bin/activate"
echo "Set JIT cache:  export TORCH_EXTENSIONS_DIR=${TORCH_EXT_DIR}"
