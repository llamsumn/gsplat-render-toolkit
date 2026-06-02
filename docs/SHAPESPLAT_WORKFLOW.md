# ShapeSplat / Object-level Dataset Workflow

Render standalone 3DGS objects (no cameras.json) from datasets like
[ShapeSplat](https://github.com/qimaqi/ShapeSplat-Gaussian_MAE).

## Overview

Object-level datasets provide only PLY files — one per object, centred near
the origin, with ~20-50K Gaussians each. The toolkit's orbit camera generator
creates a cameras.json that orbits the camera around the object.

## Step-by-step

### 1. Download a PLY from ShapeSplat

Get data from [HuggingFace](https://huggingface.co/datasets/ShapeSplat/ShapeSplat-Dataset).
Each category (e.g. `xbox/`) has `train/` and `test/` splits with individual
object folders, each containing a `point_cloud.ply`. Pick any one.

### 2. Generate orbit cameras (on your Mac)

```bash
cd ~/gsplat-render-toolkit

python3 scripts/generate_orbit_cameras.py \
    --ply /path/to/point_cloud.ply \
    -o cameras.json
```

The `--ply` flag auto-detects the object's centre and size, setting the orbit
radius to 3x the object extent.

Options:
```
--radius FLOAT     Override orbit radius (default: auto from PLY)
--elevation FLOAT  Camera elevation in degrees (default: 25)
--num-views INT    Number of orbit views (default: 36)
--fov FLOAT        Vertical field of view in degrees (default: 50)
--width INT        Image width (default: 800)
--height INT       Image height (default: 800)
```

### 3. Upload to Hex

```bash
# Create scene directory and upload PLY + cameras
rsync -avz /path/to/object_folder/ YOUR_USER@YOUR_NODE:/mnt/fast0/YOUR_USER/gsplat_work/SCENE_NAME/
rsync -avz cameras.json YOUR_USER@YOUR_NODE:/mnt/fast0/YOUR_USER/gsplat_work/SCENE_NAME/
```

### 4. Render on Hex

```bash
ssh YOUR_USER@YOUR_NODE
source /mnt/fast0/YOUR_USER/gsplat_env/bin/activate
export TORCH_EXTENSIONS_DIR=/mnt/fast0/YOUR_USER/torch_extensions
cd /mnt/fast0/YOUR_USER/gsplat_work/SCENE_NAME

# Test with 5 views
python3 ~/gsplat-render-toolkit/render_gsplat.py \
    --ply point_cloud.ply \
    --cameras cameras.json \
    --output renders \
    --black-bg --limit 5

# Full render (all views)
python3 ~/gsplat-render-toolkit/render_gsplat.py \
    --ply point_cloud.ply \
    --cameras cameras.json \
    --output renders \
    --black-bg
```

Use `--black-bg` for object-level renders (white background is better for
NeRF synthetic scenes like lego).

### 5. Download and make a video (on your Mac)

```bash
rsync -avz YOUR_USER@YOUR_NODE:/mnt/fast0/YOUR_USER/gsplat_work/SCENE_NAME/renders/ ./renders/
./scripts/make_video.sh ./renders orbit.mp4 30
open orbit.mp4
```

### 6. Clean up Hex

```bash
rm -rf /mnt/fast0/YOUR_USER/gsplat_work/SCENE_NAME
```

## Tips

- **Train vs test split** doesn't matter for rendering — both contain valid PLY files.
- ShapeSplat objects use **SH degree 3** (full spherical harmonics), so
  view-dependent colour effects are preserved.
- Objects are small (~20-50K Gaussians), so rendering is fast (~2 fps on RTX 3090).
- For batch rendering of many objects, loop over PLY files and generate
  cameras once (they can be reused if objects share similar scale).
