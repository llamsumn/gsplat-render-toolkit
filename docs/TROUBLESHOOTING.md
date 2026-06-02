# Troubleshooting

Common errors encountered when running gsplat on Hex, and their fixes.

## ModuleNotFoundError: No module named 'packaging'

```
File ".../gsplat/cuda/_backend.py", line 15, in <module>
    from packaging import version
ModuleNotFoundError: No module named 'packaging'
```

**Fix:** `pip install packaging`

This is a missing dependency in some gsplat versions. The `setup_hex.sh` script includes it.

## AttributeError: 'total_mem' (PyTorch >= 2.10)

```
AttributeError: '_CudaDeviceProperties' object has no attribute 'total_mem'. Did you mean: 'total_memory'?
```

**Fix:** The attribute was renamed in newer PyTorch. `render_gsplat.py` already uses `total_memory`.

## AssertionError on backgrounds shape

```
assert backgrounds.shape == image_dims + (channels,)
AssertionError: torch.Size([1, 3])
```

**Fix:** The `backgrounds` parameter API changes between gsplat versions.
`render_gsplat.py` avoids this by applying the background manually:

```python
# Instead of passing backgrounds= to rasterization():
img = renders[0] + (1.0 - alphas[0]) * bg_color
```

## screen session issues

If screen sessions freeze or accumulate:

```bash
# List sessions:
screen -ls

# Kill a specific session:
screen -X -S <session_id> quit
```

**Alternative:** Use `nohup` instead of screen (this is what `run_hex.sh` does):

```bash
nohup python3 render_gsplat.py 1> render_log.txt 2>&1 &
```

## CUDA out of memory

If you get OOM errors with very large scenes (millions of Gaussians):

1. Use a GPU with more VRAM (`nvidia-smi` to check)
2. Target a specific GPU: `CUDA_VISIBLE_DEVICES=0 python3 render_gsplat.py`
3. The script renders one camera at a time to minimise VRAM usage

## gsplat JIT compilation slow on first run

The first frame takes 5-15 seconds because gsplat compiles CUDA kernels.
Subsequent frames are fast (~0.4s each on an RTX 3090 with 300K Gaussians).

## Name collisions in renders (200 files instead of 300)

If your cameras.json has duplicate `img_name` values (e.g. train and test both
have r_0 through r_99), renders overwrite each other.

**Fix:** `render_gsplat.py` uses sequential numbering (00000.png, 00001.png, ...)
to avoid this.
