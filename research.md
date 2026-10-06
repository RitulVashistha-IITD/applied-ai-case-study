````markdown
# Research Notes

## 1. Dataset Inspection

### Dataset

Inspected:

`single_scan_with_ceiling.zip`

Files identified:

- `depth/*.png`
- `confidence/*.png`
- `odometry.csv`
- `imu.csv`
- `camera_matrix.csv`

### Depth frames

The dataset contains **9,745 depth frames**, numbered from `000000` through `009744`.

A sample depth frame (`000001.png`) was inspected:

- Resolution: 256 × 192
- Format: PNG
- Data type: uint16
- Minimum value: 740
- Maximum value: 4395
- Non-zero pixels: 49,152 / 49,152
- Mean value: 1519.86

The numerical range appears consistent with metric depth represented at a millimetre-like scale, but the exact depth unit has **not yet been confirmed**.

### Depth scaling assumption

The reconstruction currently assumes that the depth values are represented in a millimetre-like scale and converts them to metres using a scale factor of 1000.

This scale is an implementation assumption based on the observed depth-value range; the dataset metadata inspected so far does not explicitly confirm the depth unit.

### Confidence frames

The corresponding confidence frame was inspected:

- Resolution: 256 × 192
- Data type: uint8
- Minimum value: 0
- Maximum value: 2
- Unique values: 0, 1, 2
- Mean value: 1.804

The confidence map is therefore categorical with three observed values. The semantic meaning of values `0`, `1`, and `2` has not yet been established.

### Camera intrinsics

`camera_matrix.csv` contains:

```text
fx = 1601.0514
fy = 1601.0514
cx = 955.82275
cy = 717.7025
````

The reconstruction scales these intrinsic parameters from the native camera resolution to the actual depth-frame resolution.

---

## 2. Reconstruction Method

### Depth back-projection

For each valid depth pixel `(u, v)` with depth `z`, camera-space coordinates are calculated using the pinhole camera model:

```text
X = (u - cx) * z / fx
Y = (v - cy) * z / fy
Z = z
```

Invalid, non-positive, non-finite, and excessively large depth values are rejected.

Where confidence maps are available, confidence values are also used during point selection.

### Pose transformation

Camera-space points are transformed into world coordinates using the recorded camera translation and quaternion orientation.

The transformation is:

```text
p_world = R p_camera + t
```

where:

* `R` is the rotation matrix obtained from the recorded quaternion.
* `t` is the recorded translation.

### Frame sampling

The implementation processes every 30th odometry frame.

A maximum of 2,000 points is retained from each processed frame to keep reconstruction computationally manageable.

The sampled points are concatenated into a single 3D point cloud.

---

## 3. Reconstruction Results

The reconstruction pipeline was run on all three supplied LiDAR datasets.

| Dataset                    | Odometry Frames | Sampled Frames | Output Points |
| -------------------------- | --------------: | -------------: | ------------: |
| `single_room`              |           1,715 |             58 |       116,000 |
| `single_scan_floor_only`   |           5,251 |            176 |       352,000 |
| `single_scan_with_ceiling` |           9,745 |            325 |       650,000 |

### Output validation

The generated point clouds were independently checked for invalid numerical values.

| Dataset        | NaN Points | Infinite Points | All Points Finite |
| -------------- | ---------: | --------------: | ----------------- |
| `single_room`  |          0 |               0 | Yes               |
| `floor_only`   |          0 |               0 | Yes               |
| `with_ceiling` |          0 |               0 | Yes               |

All three generated point clouds therefore contain finite 3D coordinates.

---

## 4. Visualization

The reconstructed point clouds were visualized using the project visualization script.

Generated visualizations:

```text
outputs/visualizations/single_room.png
outputs/visualizations/floor_only.png
outputs/visualizations/with_ceiling.png
```

The visualization script removes invalid points before rendering and uses deterministic random sampling when the point cloud contains more than 30,000 points.

---

## 5. Implementation Assumptions

The current reconstruction makes the following assumptions:

1. Depth values are converted to metres using a scale factor of 1000.
2. Camera intrinsics are scaled to match the depth-frame resolution.
3. Recorded odometry poses correspond to the camera coordinate frame used by the depth data.
4. Quaternion orientation is converted using the standard quaternion-to-rotation-matrix representation.
5. Every 30th odometry frame is sufficient for the current prototype reconstruction.
6. A maximum of 2,000 points per processed frame provides a manageable reconstruction size.

The depth-unit assumption is explicitly documented as an assumption because the inspected dataset metadata did not independently confirm the unit.

---

## 6. Current Limitations

The current implementation is a **LiDAR reconstruction prototype** and does not yet cover the complete Round 1 product contract.

Current gaps include:

* Photo-tier reconstruction
* Video-tier reconstruction
* Whole-property multi-room floor-plan stitching
* Explicit loop-closure or accumulated-drift correction
* Wall and opening extraction
* Ceiling-height measurement
* Floor-area measurement
* Damage detection and classification
* Concealed-damage rules
* Surface-level scope line items
* Confidence intervals and measurement calibration
* Ground-truth accuracy benchmarking
* Same-room repeatability benchmarking
* Consumer scanning-app comparison
* Complete fix-loop benchmark
* Full three-tier walk-in test

These limitations are stated explicitly rather than treating unimplemented functionality as completed functionality.

---

## 7. Reproducibility

Each supplied capture can be reconstructed independently with a single command.

Example:

```bash
python3 src/reconstruct.py data/single_room.zip \
    --output outputs/single_room.npz
```

The resulting point cloud can be visualized with:

```bash
python3 src/visualize.py outputs/single_room.npz \
    --output outputs/visualizations/single_room.png
```

The same procedure can be applied to the other supplied datasets.

---

## 8. Summary

The current work establishes a reproducible LiDAR reconstruction pipeline from raw depth frames, confidence maps, camera intrinsics, and recorded poses.

The implementation successfully reconstructs and validates point clouds for all three supplied LiDAR captures. The repository documents both the implemented functionality and the remaining gaps in the broader case-study requirements.

````


