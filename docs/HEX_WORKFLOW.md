# Hex GPU Cloud Workflow

Step-by-step guide to render a 3DGS scene on the University of Bath Hex GPU cloud.

## Prerequisites

- A Hex account (see https://hex.cs.bath.ac.uk)
- A trained 3DGS scene (PLY + cameras.json), or a standalone PLY (e.g. ShapeSplat)
- SSH access to a Hex node

## First-time setup (once)

1. Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your HEX_USER and HEX_NODE
```

2. SSH into a node with a free GPU. Check https://hex.cs.bath.ac.uk/usage first.

```bash
ssh YOUR_USER@YOUR_NODE
```

3. Upload the toolkit to Hex (rsync from your Mac, since Hex may not have GitHub access):

```bash
# From your Mac:
rsync -avz ~/gsplat-render-toolkit/ YOUR_USER@YOUR_NODE:~/gsplat-render-toolkit/ --exclude .git
```

4. Run the setup script to create the Python environment:

```bash
# On Hex:
bash ~/gsplat-render-toolkit/setup_hex.sh
```

This creates the venv and JIT cache on `/mnt/fast0/` (not home) to avoid
the 25GB home quota. gsplat is compiled from source (~5-10 min) so CUDA
kernels are pre-built.

## Per-scene workflow

### 1. Upload your scene

```bash
# From your Mac (using the upload script):
./scripts/upload_to_hex.sh /path/to/your/scene scene_name

# Or manually with rsync:
rsync -avz /path/to/your/scene/ YOUR_USER@YOUR_NODE:/mnt/fast0/YOUR_USER/gsplat_work/scene_name/
```

### 2. SSH in and render

```bash
ssh YOUR_USER@YOUR_NODE
source /mnt/fast0/YOUR_USER/gsplat_env/bin/activate
export TORCH_EXTENSIONS_DIR=/mnt/fast0/YOUR_USER/torch_extensions
cd /mnt/fast0/YOUR_USER/gsplat_work/scene_name

# Quick test (5 views):
python3 ~/gsplat-render-toolkit/render_gsplat.py --limit 5

# Full render (background):
bash ~/gsplat-render-toolkit/run_hex.sh
```

You can disconnect safely. The render continues via `nohup`.

### 3. Check progress

```bash
tail -f render_log.txt
```

### 4. Download results

```bash
# From your Mac:
./scripts/download_from_hex.sh scene_name

# Or manually:
rsync -avz YOUR_USER@YOUR_NODE:/mnt/fast0/YOUR_USER/gsplat_work/scene_name/renders/ ./renders/
```

### 5. Clean up Hex

```bash
# On Hex — remove scene data (no backups exist!):
rm -rf /mnt/fast0/YOUR_USER/gsplat_work/scene_name
```

## Picking a GPU

If the node has multiple GPUs, target a specific one:

```bash
CUDA_VISIBLE_DEVICES=2 python3 ~/gsplat-render-toolkit/render_gsplat.py ...
```

Check GPU status with `nvidia-smi`.

## Home directory quota

Hex home quota is 25GB. The venv and JIT cache live on `/mnt/fast0/`
(separate, larger storage) to avoid quota issues.

Only `~/gsplat-render-toolkit` (~1MB) lives in home.

If you're done with gsplat for a while, free space:

```bash
rm -rf /mnt/fast0/YOUR_USER/gsplat_env
rm -rf /mnt/fast0/YOUR_USER/torch_extensions
# Re-create later with: bash ~/gsplat-render-toolkit/setup_hex.sh
```
