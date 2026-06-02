# Local Workflow (CUDA machine)

If you have a local machine with an NVIDIA GPU, you can skip Hex entirely.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For the PyTorch CUDA version matching your driver, see:
https://pytorch.org/get-started/locally/

## Render

```bash
cd /path/to/your/3dgs/scene
python3 /path/to/gsplat-render-toolkit/render_gsplat.py \
    --ply point_cloud/iteration_30000/point_cloud.ply \
    --cameras cameras.json \
    --output ./gsplat_renders
```

## Options

```
--ply PATH          Path to Gaussian PLY file (default: point_cloud/iteration_30000/point_cloud.ply)
--cameras PATH      Path to cameras.json (default: cameras.json)
--output PATH       Output directory (default: gsplat_renders)
--white-bg          White background (default, for NeRF synthetic scenes)
--black-bg          Black background (for real-world scenes)
--limit N           Render only first N cameras (for testing)
--device DEVICE     Torch device: cuda, cuda:0, cpu (default: cuda)
```

## Make a video

```bash
./scripts/make_video.sh ./gsplat_renders output.mp4 30
```

## Note on macOS (Apple Silicon)

gsplat requires CUDA. It does NOT work on MPS (Apple GPU).
Use Hex or a remote CUDA machine instead.
