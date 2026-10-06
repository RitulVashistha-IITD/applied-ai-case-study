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