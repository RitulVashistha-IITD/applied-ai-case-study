import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser(
        description="Visualize a reconstructed LiDAR point cloud."
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the .npz point cloud file.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the visualization as a PNG.",
    )

    args = parser.parse_args()

    data = np.load(args.input)
    points = data["points"]

    # Remove invalid values
    points = points[np.all(np.isfinite(points), axis=1)]

    print("Valid points:", len(points))
    print("Min:", points.min(axis=0))
    print("Max:", points.max(axis=0))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    # Plot a subset so matplotlib stays responsive
    if len(points) > 30000:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(points), 30000, replace=False)
        points = points[idx]

    ax.scatter(
        points[:, 0],
        points[:, 1],
        points[:, 2],
        s=0.3,
    )

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.set_title("Reconstructed LiDAR Point Cloud")

    plt.tight_layout()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(args.output, dpi=200, bbox_inches="tight")
        print(f"Saved visualization: {args.output}")
        plt.close()
    else:
        plt.show()


if __name__ == "__main__":
    main()