#!/usr/bin/env python3
"""
Generate an orbit cameras.json for rendering standalone 3DGS objects.

Produces a cameras.json compatible with render_gsplat.py by orbiting the
camera around a centre point (default: origin) at a fixed radius and elevation.

Usage:
    python3 scripts/generate_orbit_cameras.py -o examples/shapesplat/cameras.json
    python3 scripts/generate_orbit_cameras.py --radius 3.0 --elevation 30 --num-views 60 -o cameras.json

    # Auto-fit radius from a PLY file:
    python3 scripts/generate_orbit_cameras.py --ply point_cloud.ply -o cameras.json
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np


def look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray = np.array([0, 0, 1])):
    """Return a 3x3 camera-to-world rotation matrix (look-at convention)."""
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        up = np.array([0, 1, 0])
        right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    # 3DGS convention: camera X=right, Y=down, Z=forward (looks along +Z)
    R_c2w = np.stack([right, down, forward], axis=1)
    return R_c2w


def generate_cameras(
    num_views: int,
    radius: float,
    elevation_deg: float,
    centre: tuple[float, float, float],
    width: int,
    height: int,
    fov_deg: float,
) -> list[dict]:
    """Generate orbit cameras in the same format as 3DGS cameras.json."""
    el = math.radians(elevation_deg)
    target = np.array(centre, dtype=np.float64)
    fx = fy = 0.5 * width / math.tan(math.radians(fov_deg) / 2)

    cameras = []
    for i in range(num_views):
        az = 2 * math.pi * i / num_views
        eye = target + np.array([
            radius * math.cos(el) * math.cos(az),
            radius * math.cos(el) * math.sin(az),
            radius * math.sin(el),
        ])
        R_c2w = look_at(eye, target)

        cameras.append({
            "id": i,
            "img_name": f"r_{i}",
            "width": width,
            "height": height,
            "position": eye.tolist(),
            "rotation": R_c2w.tolist(),
            "fx": fx,
            "fy": fy,
        })
    return cameras


def auto_radius_from_ply(ply_path: Path) -> tuple[float, tuple[float, float, float]]:
    """Read a PLY and return (suggested_radius, centroid)."""
    from plyfile import PlyData
    ply = PlyData.read(str(ply_path))
    v = ply["vertex"]
    xyz = np.stack([v["x"], v["y"], v["z"]], axis=-1).astype(np.float64)
    centroid = xyz.mean(axis=0)
    max_dist = np.linalg.norm(xyz - centroid, axis=-1).max()
    radius = max_dist * 3.0
    return radius, tuple(centroid.tolist())


def main():
    p = argparse.ArgumentParser(
        description="Generate orbit cameras.json for standalone 3DGS objects.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("-o", "--output", type=Path, required=True, help="Output cameras.json path.")
    p.add_argument("--ply", type=Path, default=None, help="PLY file to auto-fit radius and centre from.")
    p.add_argument("--radius", type=float, default=None, help="Camera orbit radius. Overrides --ply auto-fit.")
    p.add_argument("--elevation", type=float, default=25.0, help="Camera elevation in degrees.")
    p.add_argument("--num-views", type=int, default=36, help="Number of orbit views.")
    p.add_argument("--width", type=int, default=800, help="Image width.")
    p.add_argument("--height", type=int, default=800, help="Image height.")
    p.add_argument("--fov", type=float, default=50.0, help="Vertical field of view in degrees.")
    args = p.parse_args()

    centre = (0.0, 0.0, 0.0)
    radius = args.radius

    if args.ply:
        auto_r, auto_c = auto_radius_from_ply(args.ply)
        if radius is None:
            radius = auto_r
        centre = auto_c
        print(f"PLY centroid: ({centre[0]:.3f}, {centre[1]:.3f}, {centre[2]:.3f})")
        print(f"Auto radius:  {auto_r:.3f}" + ("  (overridden)" if args.radius else ""))

    if radius is None:
        radius = 3.0

    print(f"Generating {args.num_views} cameras: radius={radius:.3f}, elevation={args.elevation}°, fov={args.fov}°")

    cameras = generate_cameras(
        num_views=args.num_views,
        radius=radius,
        elevation_deg=args.elevation,
        centre=centre,
        width=args.width,
        height=args.height,
        fov_deg=args.fov,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(cameras, f, indent=2)
    print(f"Wrote {len(cameras)} cameras to {args.output}")


if __name__ == "__main__":
    main()
