#! /usr/bin/env python3
"""
Render a 3D Gaussian Splatting scene using gsplat.

Loads a standard 3DGS PLY (from graphdeco-inria/gaussian-splatting) and the
accompanying cameras.json, then rasterises every camera with gsplat and saves
the resulting images.

Requirements (install inside your venv / Docker container):
    pip install gsplat plyfile torch torchvision numpy Pillow

Usage:
    python3 render_gsplat.py \
        --ply  point_cloud/iteration_30000/point_cloud.ply \
        --cameras cameras.json \
        --output ./gsplat_renders

    # Render only the first 10 cameras (useful for a quick sanity-check):
    python3 render_gsplat.py --ply ... --cameras ... --output ... --limit 10

    # Use a specific GPU when multiple are visible:
    CUDA_VISIBLE_DEVICES=2 python3 render_gsplat.py ...
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from plyfile import PlyData

# gsplat's main entry point
from gsplat import rasterization

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PLY loading
# ---------------------------------------------------------------------------

def load_ply(path: Path, device: torch.device) -> dict[str, torch.Tensor]:
    """Load a standard 3DGS PLY and return tensors ready for gsplat."""
    log.info("Loading PLY from %s …", path)
    ply = PlyData.read(str(path))
    v = ply["vertex"]
    n = len(v["x"])
    log.info("  %d Gaussians", n)

    # --- positions (N, 3) ---
    means = torch.tensor(
        np.stack([v["x"], v["y"], v["z"]], axis=-1),
        dtype=torch.float32,
        device=device,
    )

    # --- quaternions (N, 4)  wxyz order — same as the PLY ---
    quats = torch.tensor(
        np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], axis=-1),
        dtype=torch.float32,
        device=device,
    )

    # --- scales (N, 3)  stored as log(scale) in the PLY → exp to get actual ---
    scales = torch.exp(
        torch.tensor(
            np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], axis=-1),
            dtype=torch.float32,
            device=device,
        )
    )

    # --- opacities (N,)  stored as logit(opacity) in the PLY → sigmoid ---
    opacities = torch.sigmoid(
        torch.tensor(
            np.array(v["opacity"]),
            dtype=torch.float32,
            device=device,
        )
    )

    # --- spherical-harmonics coefficients (N, K, 3) ---
    # DC term: f_dc_{0,1,2}  → shape (N, 1, 3)
    sh_dc = torch.tensor(
        np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], axis=-1),
        dtype=torch.float32,
        device=device,
    ).unsqueeze(1)  # (N, 1, 3)

    # Count how many f_rest_* properties exist to infer SH degree
    rest_names = sorted(
        [p.name for p in ply["vertex"].properties if p.name.startswith("f_rest_")],
        key=lambda n: int(n.split("_")[-1]),
    )
    num_rest = len(rest_names)  # 45 for degree 3, 24 for degree 2, 9 for degree 1

    if num_rest > 0:
        rest_flat = torch.tensor(
            np.stack([v[name] for name in rest_names], axis=-1),
            dtype=torch.float32,
            device=device,
        )  # (N, num_rest)
        # The PLY flattens (N, num_rest//3, 3) row-major:
        #   f_rest_0 = band1_ch0, f_rest_1 = band1_ch1, f_rest_2 = band1_ch2, …
        sh_rest = rest_flat.reshape(n, num_rest // 3, 3)  # (N, num_rest//3, 3)
        sh_coeffs = torch.cat([sh_dc, sh_rest], dim=1)    # (N, K, 3)
    else:
        sh_coeffs = sh_dc  # degree-0 only

    num_bands = sh_coeffs.shape[1]  # (degree+1)^2
    sh_degree = int(num_bands**0.5) - 1
    log.info("  SH degree %d  (%d coefficients per channel)", sh_degree, num_bands)

    return dict(
        means=means,
        quats=quats,
        scales=scales,
        opacities=opacities,
        sh_coeffs=sh_coeffs,
        sh_degree=sh_degree,
    )


# ---------------------------------------------------------------------------
# Camera loading
# ---------------------------------------------------------------------------

def load_cameras(path: Path) -> list[dict]:
    """
    Load cameras.json produced by the original 3DGS training code.

    Each entry contains:
        position  – camera centre in **world** coordinates
        rotation  – camera-to-world rotation (3×3)
        fx, fy    – focal lengths in pixels
        width, height
    """
    log.info("Loading cameras from %s …", path)
    with open(path) as f:
        cams = json.load(f)
    log.info("  %d cameras", len(cams))
    return cams


def build_view_and_K(
    cam: dict, device: torch.device
) -> tuple[torch.Tensor, torch.Tensor, int, int]:
    """
    Return (viewmat [4,4], K [3,3], width, height) for one camera entry.

    The original 3DGS code serialises cameras.json as follows:
        C2W = [R^T | T; 0 0 0 1]  then  W2C = inv(C2W)
        position = W2C[:3, 3]   → but this is actually the camera-to-world
                                   translation (camera centre in world coords)
        rotation = W2C[:3, :3]  → camera-to-world rotation

    (The variable name "W2C" in the upstream code is misleading — it's actually
    the camera-to-world matrix from which pos and rot are extracted.)

    So to recover the true world-to-camera matrix we invert:
        R_w2c = rotation^T
        t_w2c = -R_w2c @ position
    """
    R_c2w = np.array(cam["rotation"], dtype=np.float64)   # (3, 3)
    pos   = np.array(cam["position"], dtype=np.float64)    # (3,)

    R_w2c = R_c2w.T
    t_w2c = -R_w2c @ pos

    viewmat = np.eye(4, dtype=np.float64)
    viewmat[:3, :3] = R_w2c
    viewmat[:3, 3]  = t_w2c

    w = cam["width"]
    h = cam["height"]
    fx = cam["fx"]
    fy = cam["fy"]
    cx = w / 2.0
    cy = h / 2.0

    K = np.array(
        [[fx,  0.0, cx],
         [0.0, fy,  cy],
         [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )

    return (
        torch.tensor(viewmat, dtype=torch.float32, device=device),
        torch.tensor(K, dtype=torch.float32, device=device),
        w,
        h,
    )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

@torch.no_grad()
def render_cameras(
    gaussians: dict[str, torch.Tensor],
    cameras: list[dict],
    output_dir: Path,
    device: torch.device,
    bg_color: tuple[float, float, float] = (1.0, 1.0, 1.0),
    limit: int | None = None,
) -> None:
    """Render each camera and save the result as a PNG."""
    output_dir.mkdir(parents=True, exist_ok=True)

    means     = gaussians["means"]
    quats     = gaussians["quats"]
    scales    = gaussians["scales"]
    opacities = gaussians["opacities"]
    sh_coeffs = gaussians["sh_coeffs"]
    sh_degree = gaussians["sh_degree"]

    total = len(cameras) if limit is None else min(limit, len(cameras))
    log.info("Rendering %d views  (background=%.1f,%.1f,%.1f) …", total, *bg_color)

    t0 = time.perf_counter()

    for idx, cam in enumerate(cameras[:total]):
        viewmat, K, w, h = build_view_and_K(cam, device)

        renders, alphas, _meta = rasterization(
            means=means,
            quats=quats,
            scales=scales,
            opacities=opacities,
            colors=sh_coeffs,
            viewmats=viewmat.unsqueeze(0),       # (1, 4, 4)
            Ks=K.unsqueeze(0),                    # (1, 3, 3)
            width=w,
            height=h,
            sh_degree=sh_degree,
            near_plane=0.01,
            far_plane=100.0,
        )
        # renders: (1, H, W, 3), alphas: (1, H, W, 1)
        # Apply background manually — avoids version-dependent backgrounds API
        bg = torch.tensor(bg_color, dtype=torch.float32, device=device)
        img = (renders[0] + (1.0 - alphas[0]) * bg).clamp(0.0, 1.0).cpu().numpy()
        img_uint8 = (img * 255.0 + 0.5).astype(np.uint8)

        # Use sequential index to avoid name collisions (train/test both have r_0..r_99)
        out_path = output_dir / f"{idx:05d}.png"
        Image.fromarray(img_uint8).save(out_path)

        elapsed = time.perf_counter() - t0
        fps = (idx + 1) / elapsed
        log.info(
            "  [%d/%d]  %s  (%.1f fps, %.1f s elapsed)",
            idx + 1,
            total,
            out_path.name,
            fps,
            elapsed,
        )

    total_time = time.perf_counter() - t0
    log.info("Done — %d images in %.1f s (%.2f fps avg)", total, total_time, total / total_time)
    log.info("Saved to %s", output_dir.resolve())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Render a 3DGS scene with gsplat.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--ply",
        type=Path,
        default=Path("point_cloud/iteration_30000/point_cloud.ply"),
        help="Path to the Gaussian PLY file.",
    )
    p.add_argument(
        "--cameras",
        type=Path,
        default=Path("cameras.json"),
        help="Path to cameras.json from 3DGS training.",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("gsplat_renders"),
        help="Directory for rendered PNGs.",
    )
    p.add_argument(
        "--white-bg",
        action="store_true",
        default=True,
        help="Use white background (default for NeRF-synthetic).",
    )
    p.add_argument(
        "--black-bg",
        action="store_true",
        default=False,
        help="Use black background instead of white.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only render the first N cameras (for quick testing).",
    )
    p.add_argument(
        "--device",
        type=str,
        default="cuda",
        help="Torch device (cuda, cuda:0, cpu, …).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Validate inputs exist
    if not args.ply.exists():
        log.error("PLY not found: %s", args.ply)
        sys.exit(1)
    if not args.cameras.exists():
        log.error("cameras.json not found: %s", args.cameras)
        sys.exit(1)

    device = torch.device(args.device)
    log.info("Using device: %s", device)

    if device.type == "cuda":
        log.info(
            "GPU: %s  (%.1f GB)",
            torch.cuda.get_device_name(device),
            torch.cuda.get_device_properties(device).total_memory / 1e9,
        )

    bg = (0.0, 0.0, 0.0) if args.black_bg else (1.0, 1.0, 1.0)

    gaussians = load_ply(args.ply, device)
    cameras   = load_cameras(args.cameras)

    render_cameras(
        gaussians=gaussians,
        cameras=cameras,
        output_dir=args.output,
        device=device,
        bg_color=bg,
        limit=args.limit,
    )

    log.info("Remember to copy results off the cloud — there are no backups!")


if __name__ == "__main__":
    main()
