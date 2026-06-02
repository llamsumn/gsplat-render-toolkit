# Lego Example Scene

NeRF Synthetic Lego bulldozer, trained with the original
[3D Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting) codebase.

## Scene details

| Property | Value |
|---|---|
| Gaussians | 300,257 |
| SH degree | 3 (16 coefficients per channel) |
| Cameras | 300 (200 train + 100 test) |
| Resolution | 800 x 800 |
| Focal length | fx = fy = 1111.11 |
| Background | White |
| PLY size | 71 MB |

## Training metrics (iteration 30,000)

| Metric | Value |
|---|---|
| PSNR | 35.94 dB |
| SSIM | 0.983 |
| LPIPS | 0.015 |

## Render performance (gsplat 1.5.3)

| GPU | FPS | Total time (300 views) |
|---|---|---|
| RTX 3090 (Hex) | 2.4 - 2.6 | ~2 min |

## Quick test

```bash
cd examples/lego
python3 ../../render_gsplat.py --limit 5
```
