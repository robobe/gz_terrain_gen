import csv
import math
from pathlib import Path

import rasterio
from rasterio.windows import from_bounds

DEFAULT_TILE_M = 200
MANIFEST_FIELDS = [
    "file",
    "tile_x",
    "tile_y",
    "west",
    "south",
    "east",
    "north",
    "gazebo_corner_x_m",
    "gazebo_corner_y_m",
    "gazebo_center_x_m",
    "gazebo_center_y_m",
]


def split_dem(input_path: Path, tiles_dir: Path, tile_m: int = DEFAULT_TILE_M) -> tuple[int, Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"missing DEM: {input_path}")

    tiles_dir.mkdir(parents=True, exist_ok=True)
    tile_count = 0
    manifest_path = tiles_dir / "tiles.csv"

    with rasterio.open(input_path) as src:
        west, south, east, north = src.bounds
        center_lat = (south + north) / 2.0
        tile_lat_deg = tile_m / 111_320.0
        tile_lon_deg = tile_m / (111_320.0 * math.cos(math.radians(center_lat)))

        with manifest_path.open("w", newline="") as manifest:
            writer = csv.DictWriter(manifest, fieldnames=MANIFEST_FIELDS)
            writer.writeheader()

            tile_y = 0
            y = south
            while y < north:
                tile_x = 0
                x = west
                while x < east:
                    x2 = min(x + tile_lon_deg, east)
                    y2 = min(y + tile_lat_deg, north)
                    window = from_bounds(
                        left=x,
                        bottom=y,
                        right=x2,
                        top=y2,
                        transform=src.transform,
                    ).round_offsets().round_lengths()

                    if window.width > 0 and window.height > 0:
                        profile = src.profile.copy()
                        profile.update(
                            width=window.width,
                            height=window.height,
                            transform=src.window_transform(window),
                        )

                        file_name = f"tile_{tile_x}_{tile_y}.tif"
                        out_path = tiles_dir / file_name
                        with rasterio.open(out_path, "w", **profile) as dst:
                            dst.write(src.read(window=window))

                        writer.writerow(
                            {
                                "file": file_name,
                                "tile_x": tile_x,
                                "tile_y": tile_y,
                                "west": x,
                                "south": y,
                                "east": x2,
                                "north": y2,
                                "gazebo_corner_x_m": tile_x * tile_m,
                                "gazebo_corner_y_m": tile_y * tile_m,
                                "gazebo_center_x_m": (tile_x + 0.5) * tile_m,
                                "gazebo_center_y_m": (tile_y + 0.5) * tile_m,
                            }
                        )
                        tile_count += 1

                    tile_x += 1
                    x += tile_lon_deg
                tile_y += 1
                y += tile_lat_deg

    return tile_count, manifest_path
