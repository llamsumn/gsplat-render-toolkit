# gsplat-render-toolkit

Render 3D Gaussian Splatting scenes using [gsplat](https://github.com/nerfstudio-project/gsplat). Includes helper scripts for running on the University of Bath Hex GPU cloud.

## What this does

Takes a trained 3DGS model (PLY + cameras.json from [gaussian-splatting](https://github.com/graphdeco-inria/gaussian-splatting)) and renders images from every camera viewpoint using gsplat's CUDA rasteriser.

Also supports **object-level datasets** like [ShapeSplat](https://github.com/qimaqi/ShapeSplat-Gaussian_MAE) — use the included orbit camera generator to render standalone PLY files that don't come with cameras.

https://github.com/user-attachments/assets/c7abb16d-4ba6-409b-a796-a06993f235b4

## Quick start

```bash
# 1. Set up your environment (on a CUDA machine or Hex)
bash setup_hex.sh

# 2. Render a scene
cd /path/to/your/3dgs/scene
python3 /path/to/render_gsplat.py --limit 5     # test
python3 /path/to/render_gsplat.py                # full render
```

## Repo structure

```
render_gsplat.py          Main render script
setup_hex.sh              One-command environment setup for Hex
run_hex.sh                Background render launcher for Hex
requirements.txt          Python dependencies

docs/
  HEX_WORKFLOW.md         Full Hex cloud guide (upload, render, download)
  LOCAL_WORKFLOW.md        Running on a local CUDA machine
  SHAPESPLAT_WORKFLOW.md  Rendering object-level datasets (ShapeSplat etc.)
  TROUBLESHOOTING.md      Common errors and fixes

scripts/
  generate_orbit_cameras.py  Generate cameras.json for standalone PLY objects
  upload_to_hex.sh           rsync wrapper: Mac -> Hex
  download_from_hex.sh       rsync wrapper: Hex -> Mac
  make_video.sh              ffmpeg: frames -> mp4

examples/
  lego/                   Example scene with PLY, cameras, and sample renders
```

## Requirements

- Python 3.10+
- NVIDIA GPU with CUDA 11.8+
- gsplat, PyTorch, plyfile, Pillow

Does NOT work on CPU or Apple MPS — CUDA is required.

## Render options

```
python3 render_gsplat.py --help

--ply PATH          Gaussian PLY file (default: point_cloud/iteration_30000/point_cloud.ply)
--cameras PATH      cameras.json from 3DGS (default: cameras.json)
--output PATH       Output directory (default: gsplat_renders)
--white-bg          White background (default)
--black-bg          Black background
--limit N           Render only first N cameras
--device DEVICE     cuda, cuda:0, cpu (default: cuda)
```

## Hex workflow (short version)

```bash
cp .env.example .env                            # fill in HEX_USER, HEX_NODE
./scripts/upload_to_hex.sh ./my_scene           # upload
ssh $HEX_USER@$HEX_NODE                        # connect
source /mnt/fast0/$USER/gsplat_env/bin/activate  # activate venv
export TORCH_EXTENSIONS_DIR=/mnt/fast0/$USER/torch_extensions
bash ~/gsplat-render-toolkit/run_hex.sh         # render (background)
exit                                            # disconnect safely
./scripts/download_from_hex.sh my_scene         # download results
```

See [docs/HEX_WORKFLOW.md](docs/HEX_WORKFLOW.md) for the full guide.

## Object-level datasets (ShapeSplat etc.)

```bash
# Generate orbit cameras from a standalone PLY
python3 scripts/generate_orbit_cameras.py --ply object.ply -o cameras.json

# Render (on a CUDA machine)
python3 render_gsplat.py --ply object.ply --cameras cameras.json --black-bg
```

See [docs/SHAPESPLAT_WORKFLOW.md](docs/SHAPESPLAT_WORKFLOW.md) for the full guide.
