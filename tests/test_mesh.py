from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from gz_terrain_gen.mesh import open_dem, source_z_offset, tile_to_mesh, valid_elevation_min


def write_raster(path: Path, data: np.ndarray, transform) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)


def test_valid_elevation_min_ignores_nodata_and_nan() -> None:
    elevation = np.array([[np.nan, -9999.0], [12.0, 20.0]])

    assert valid_elevation_min(elevation, -9999.0) == 12.0


def test_tile_to_mesh_normalizes_minimum_elevation_to_zero(tmp_path: Path) -> None:
    dem_path = tmp_path / "dem.tif"
    tiles_dir = tmp_path / "tiles"
    tiles_dir.mkdir()
    tile_path = tiles_dir / "tile_0_0.tif"
    data = np.array([[10.0, 20.0]], dtype=np.float32)

    write_raster(dem_path, data, from_origin(0, 1, 1, 1))
    write_raster(tile_path, data, from_origin(0, 1, 1, 1))

    tile = {
        "file": "tile_0_0.tif",
        "west": "0",
        "south": "0",
        "east": "2",
        "north": "1",
        "gazebo_corner_x_m": "0",
        "gazebo_corner_y_m": "0",
        "gazebo_center_x_m": "10",
        "gazebo_center_y_m": "5",
    }
    source = open_dem(dem_path)

    vertices, _faces = tile_to_mesh(tile, source, tiles_dir)
    z_values = [vertex[2] for vertex in vertices]

    assert source_z_offset(source) == 10.0
    assert min(z_values) == 0.0
    assert max(z_values) == 10.0
