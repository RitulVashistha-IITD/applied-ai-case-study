"""
LiDAR reconstruction pipeline.

Input:
    A sample capture ZIP containing:
      - depth/*.png
      - confidence/*.png
      - odometry.csv

Output:
    outputs/point_cloud.npz

The pipeline:
    1. Reads depth frames directly from the ZIP.
    2. Reads per-frame camera intrinsics and camera poses.
    3. Back-projects depth pixels into 3D camera coordinates.
    4. Transforms camera points into world coordinates.
    5. Saves the resulting point cloud.

This is the first vertical slice of the full reconstruction system.
"""

from __future__ import annotations

import argparse
import csv
import io
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.spatial.transform import Rotation


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEPTH_SCALE = 1000.0

# The supplied depth images are 256x192. The intrinsics in odometry.csv
# correspond to the higher-resolution camera coordinate system.
# We use the common 1920x1440 source resolution and scale intrinsics down.
NATIVE_WIDTH = 1920
NATIVE_HEIGHT = 1440

# Process approximately every Nth frame.
FRAME_STRIDE = 30

# Maximum number of sampled depth pixels per frame.
MAX_POINTS_PER_FRAME = 2000


# ---------------------------------------------------------------------------
# Dataset utilities
# ---------------------------------------------------------------------------

def find_dataset_root(zf: zipfile.ZipFile) -> str:
    """Find the root directory containing depth/ and odometry.csv."""

    names = zf.namelist()

    roots = set()

    for name in names:
        parts = name.split("/")

        if len(parts) >= 2:
            roots.add(parts[0])

    for root in sorted(roots):
        if (
            f"{root}/odometry.csv" in names
            and any(name.startswith(f"{root}/depth/") for name in names)
        ):
            return root

    raise RuntimeError(
        "Could not find dataset root containing odometry.csv and depth/."
    )


def read_odometry(zf: zipfile.ZipFile, root: str) -> list[dict]:
    """Read odometry.csv into dictionaries."""

    path = f"{root}/odometry.csv"

    with zf.open(path) as f:
        text = io.TextIOWrapper(f, encoding="utf-8")
        reader = csv.DictReader(text, skipinitialspace=True)

        rows = []

        for row in reader:
            rows.append(row)

    return rows


def load_depth(
    zf: zipfile.ZipFile,
    root: str,
    frame: str,
) -> np.ndarray:
    """Load a single depth image."""

    path = f"{root}/depth/{frame}.png"

    with zf.open(path) as f:
        image = Image.open(f)
        return np.asarray(image, dtype=np.uint16)


def load_confidence(
    zf: zipfile.ZipFile,
    root: str,
    frame: str,
) -> np.ndarray:
    """Load a confidence image."""

    path = f"{root}/confidence/{frame}.png"

    with zf.open(path) as f:
        image = Image.open(f)
        return np.asarray(image, dtype=np.uint8)


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def get_intrinsics(row: dict, width: int, height: int):
    """
    Get camera intrinsics for the depth image resolution.

    odometry.csv stores intrinsics in the higher-resolution camera coordinate
    system, so we scale them to the 256x192 depth image.
    """

    fx = float(row["fx"])
    fy = float(row["fy"])
    cx = float(row["cx"])
    cy = float(row["cy"])

    scale_x = width / NATIVE_WIDTH
    scale_y = height / NATIVE_HEIGHT

    fx *= scale_x
    fy *= scale_y
    cx *= scale_x
    cy *= scale_y

    return fx, fy, cx, cy


def backproject_depth(
    depth: np.ndarray,
    fx: float,
    fy: float,
    cx: float,
    cy: float,
    confidence: np.ndarray | None = None,
) -> np.ndarray:
    """
    Convert a depth image into 3D camera-space points.

    Coordinate convention:
        X = horizontal
        Y = vertical
        Z = depth
    """

    height, width = depth.shape

    # Sample every few pixels to keep the point cloud manageable.
    step = 4

    v, u = np.mgrid[
        0:height:step,
        0:width:step,
    ]

    depth_values = depth[::step, ::step].astype(np.float32)

    valid = (
        np.isfinite(depth_values)
        & (depth_values > 0)
        & (depth_values < 10000)
    )

    # Confidence value 0 is treated as invalid.
    # We don't assume what values 1 and 2 specifically mean.
    if confidence is not None:
        confidence_values = confidence[::step, ::step]
        valid &= confidence_values > 0

    u = u[valid].astype(np.float32)
    v = v[valid].astype(np.float32)
    z = depth_values[valid] / DEPTH_SCALE

    x = (u - cx) * z / fx
    y = (v - cy) * z / fy

    points = np.column_stack((x, y, z))

    return points


def transform_points(
    points: np.ndarray,
    row: dict,
) -> np.ndarray:
    """Transform camera-space points into world coordinates."""

    translation = np.array(
        [
            float(row["x"]),
            float(row["y"]),
            float(row["z"]),
        ],
        dtype=np.float32,
    )

    quaternion = np.array(
        [
            float(row["qx"]),
            float(row["qy"]),
            float(row["qz"]),
            float(row["qw"]),
        ],
        dtype=np.float64,
    )

    rotation = Rotation.from_quat(quaternion).as_matrix()

    # Remove any invalid camera-space points before transformation
    points = points[np.all(np.isfinite(points), axis=1)]

    # Camera point p -> world point R p + t
    world_points = points @ rotation.T
    world_points += translation

    return world_points
# ---------------------------------------------------------------------------
# Reconstruction
# ---------------------------------------------------------------------------

def reconstruct(zip_path: Path) -> np.ndarray:
    """Build a world-space point cloud from the capture ZIP."""

    print(f"Opening dataset: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:

        root = find_dataset_root(zf)

        print(f"Dataset root: {root}")

        rows = read_odometry(zf, root)

        print(f"Odometry frames: {len(rows)}")

        all_points = []

        selected_rows = rows[::FRAME_STRIDE]

        print(
            f"Processing {len(selected_rows)} frames "
            f"(stride={FRAME_STRIDE})..."
        )

        for index, row in enumerate(selected_rows):

            frame = row["frame"]

            try:
                depth = load_depth(zf, root, frame)
                confidence = load_confidence(zf, root, frame)

            except KeyError:
                print(f"Skipping missing frame: {frame}")
                continue

            height, width = depth.shape

            fx, fy, cx, cy = get_intrinsics(
                row,
                width,
                height,
            )

            if not all(np.isfinite(v) for v in [fx, fy, cx, cy]):
                print(f"Skipping frame {frame}: invalid intrinsics")
                continue

            if fx <= 0 or fy <= 0:
                print(f"Skipping frame {frame}: invalid focal length")
                continue

            camera_points = backproject_depth(
                depth,
                fx,
                fy,
                cx,
                cy,
                confidence,
            )

            if len(camera_points) == 0:
                continue

            # Randomly cap the number of points per frame.
            if len(camera_points) > MAX_POINTS_PER_FRAME:

                indices = np.random.default_rng(index).choice(
                    len(camera_points),
                    size=MAX_POINTS_PER_FRAME,
                    replace=False,
                )

                camera_points = camera_points[indices]

            world_points = transform_points(
                camera_points,
                row,
            )

            all_points.append(world_points)

            if (index + 1) % 20 == 0 or index == 0:
                print(
                    f"  {index + 1}/{len(selected_rows)} frames "
                    f"-> {len(world_points)} points"
                )

        if not all_points:
            raise RuntimeError("No valid points were reconstructed.")

        point_cloud = np.concatenate(
            all_points,
            axis=0,
        )

    return point_cloud


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description="Reconstruct a point cloud from a LiDAR capture ZIP."
    )

    parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the capture ZIP.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/point_cloud.npz"),
        help="Output point cloud path.",
    )

    args = parser.parse_args()

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    point_cloud = reconstruct(args.dataset)

    np.savez_compressed(
        args.output,
        points=point_cloud,
    )

    print()
    print("Reconstruction complete.")
    print(f"Points: {len(point_cloud):,}")
    print(f"Output: {args.output}")

    print()
    print("Bounds:")
    print("  min:", point_cloud.min(axis=0))
    print("  max:", point_cloud.max(axis=0))


if __name__ == "__main__":
    main()