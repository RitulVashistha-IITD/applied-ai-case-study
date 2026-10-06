# Applied AI Engineer — LiDAR Reconstruction

## Overview

This project implements a LiDAR-based 3D reconstruction pipeline from raw depth frames, confidence maps, camera intrinsics, and camera poses.

The current implementation focuses on the LiDAR input tier and reconstructs a 3D point cloud by:

1. Loading depth, confidence, and odometry data from the supplied dataset ZIP.
2. Sampling depth frames at a fixed stride.
3. Back-projecting valid depth pixels into camera-space 3D coordinates.
4. Transforming camera-space points into world coordinates using the recorded pose.
5. Aggregating the reconstructed points into a single point cloud.
6. Saving the result as a compressed `.npz` file.
7. Providing a 3D visualization of the reconstructed point cloud.

## Current Scope

The current prototype implements the LiDAR reconstruction stage.

### Implemented

- Depth-frame loading
- Confidence-map filtering
- Camera intrinsic scaling
- Depth back-projection
- Quaternion-based pose transformation
- Frame sampling
- Point-count limiting
- Point-cloud aggregation
- `.npz` output
- 3D point-cloud visualization

The current prototype does not yet implement the complete Round 1 product contract, including photo/video tiers, multi-room floor-plan stitching, damage classification, opening detection, calibrated measurement intervals, or consumer-app comparison.

## Project Structure

```text
applied-ai-case-study/
├── data/
│   ├── single_room.zip
│   ├── single_scan_floor_only.zip
│   └── single_scan_with_ceiling.zip
├── outputs/
│   ├── single_room.npz
│   ├── floor_only.npz
│   ├── with_ceiling.npz
│   └── visualizations/
│       ├── single_room.png
│       ├── floor_only.png
│       └── with_ceiling.png
├── src/
│   ├── reconstruct.py
│   └── visualize.py
├── research.md
└── README.md
````

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required Python packages:

```bash
pip install numpy scipy pillow matplotlib
```

## Reconstruction

Each capture can be reconstructed independently.

### Single Room

```bash
python3 src/reconstruct.py data/single_room.zip \
    --output outputs/single_room.npz
```

### Floor-Only Scan

```bash
python3 src/reconstruct.py data/single_scan_floor_only.zip \
    --output outputs/floor_only.npz
```

### Scan With Ceiling

```bash
python3 src/reconstruct.py data/single_scan_with_ceiling.zip \
    --output outputs/with_ceiling.npz
```

## Visualization

Visualizations can be displayed interactively:

```bash
python3 src/visualize.py outputs/single_room.npz
```

Visualizations can also be saved as PNG files:

```bash
python3 src/visualize.py outputs/single_room.npz \
    --output outputs/visualizations/single_room.png
```

```bash
python3 src/visualize.py outputs/floor_only.npz \
    --output outputs/visualizations/floor_only.png
```

```bash
python3 src/visualize.py outputs/with_ceiling.npz \
    --output outputs/visualizations/with_ceiling.png
```

## Current Results

The three supplied captures were successfully reconstructed.

| Dataset                    | Odometry Frames | Sampled Frames | Output Points |
| -------------------------- | --------------: | -------------: | ------------: |
| `single_room`              |           1,715 |             58 |       116,000 |
| `single_scan_floor_only`   |           5,251 |            176 |       352,000 |
| `single_scan_with_ceiling` |           9,745 |            325 |       650,000 |

The generated point clouds were independently validated.

| Dataset        | NaN Points | Infinite Points | All Points Finite |
| -------------- | ---------: | --------------: | ----------------- |
| `single_room`  |          0 |               0 | Yes               |
| `floor_only`   |          0 |               0 | Yes               |
| `with_ceiling` |          0 |               0 | Yes               |

## Reconstruction Method

### 1. Depth Processing

Depth frames are loaded from the dataset and converted to floating-point values.

The current implementation assumes the depth values are represented in a millimetre-like scale and converts them to metres using:

```text
depth / 1000
```

Invalid, non-positive, and excessively large depth values are rejected.

Where confidence maps are available, confidence values are also used during point selection.

### 2. Camera-Space Back-Projection

For each valid depth pixel `(u, v)` with depth `z`, the camera-space coordinates are computed using the pinhole camera model:

```text
X = (u - cx) * z / fx
Y = (v - cy) * z / fy
Z = z
```

The camera intrinsics are scaled from the native camera resolution to the depth-frame resolution.

### 3. Pose Transformation

The camera-space points are transformed into world coordinates using the recorded camera translation and quaternion orientation.

The transformation is:

```text
p_world = R p_camera + t
```

where `R` is the rotation matrix obtained from the quaternion and `t` is the recorded translation.

### 4. Frame Sampling

To keep reconstruction computationally manageable, every 30th odometry frame is processed.

A maximum of 2,000 points is retained from each processed frame.

The resulting points are concatenated into a single point cloud.

## Reconstruction Assumptions

* Depth is converted to metres using a scale factor of 1000.
* Camera intrinsics are scaled to the depth-frame resolution.
* Frames are sampled every 30 odometry frames.
* A maximum of 2,000 points is retained per processed frame.
* Recorded camera poses are used to transform camera-space points into world coordinates.
* The current output is a 3D point cloud rather than a complete floor-plan representation.

## Known Limitations

The current implementation is a LiDAR reconstruction prototype and does not yet cover the complete Round 1 case-study contract.

Current gaps include:

* Photo-tier reconstruction
* Video-tier reconstruction
* Whole-property multi-room floor-plan stitching
* Explicit loop-closure or accumulated-drift correction
* Wall and opening extraction
* Ceiling-height measurement
* Damage detection and classification
* Concealed-damage rules
* Surface-level scope line items
* Confidence intervals and calibration
* Ground-truth accuracy benchmarking
* Same-room repeatability benchmarking
* Consumer scanning-app comparison
* Complete fix-loop benchmark
* Full walk-in test across all three input tiers

These limitations are stated explicitly rather than treating unimplemented functionality as completed functionality.

## Research

Dataset inspection, depth statistics, confidence-map analysis, and camera-intrinsic observations are documented in:

```text
research.md
```

## Reproducibility

The reconstruction pipeline is deterministic for a given input dataset and configuration.

Each capture can be reproduced with a single command using `src/reconstruct.py` and the corresponding dataset ZIP.

The visualization pipeline accepts a generated `.npz` file and can either display the point cloud interactively or save a PNG representation.


