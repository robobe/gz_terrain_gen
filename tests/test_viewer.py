import csv
from pathlib import Path

import numpy as np
import rasterio
from click.testing import CliRunner
from rasterio.transform import from_origin

from gz_terrain_gen.viewer import build_combined_terrain_mesh, generate_viewer, viewer_cli


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


def write_manifest(path: Path) -> None:
    rows = [
        {
            "file": "tile_0_0.tif",
            "tile_x": "0",
            "tile_y": "0",
            "west": "0",
            "south": "0",
            "east": "1",
            "north": "1",
            "gazebo_corner_x_m": "0",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "5",
            "gazebo_center_y_m": "5",
        },
        {
            "file": "tile_1_0.tif",
            "tile_x": "1",
            "tile_y": "0",
            "west": "1",
            "south": "0",
            "east": "2",
            "north": "1",
            "gazebo_corner_x_m": "10",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "15",
            "gazebo_center_y_m": "5",
        },
    ]
    with path.open("w", newline="") as manifest:
        writer = csv.DictWriter(manifest, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_viewer_inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    dem_path = tmp_path / "dem.tif"
    tiles_dir = tmp_path / "tiles"
    manifest_path = tiles_dir / "tiles.csv"
    tiles_dir.mkdir()

    write_raster(dem_path, np.array([[10.0, 20.0]], dtype=np.float32), from_origin(0, 1, 1, 1))
    write_raster(tiles_dir / "tile_0_0.tif", np.array([[10.0]], dtype=np.float32), from_origin(0, 1, 1, 1))
    write_raster(tiles_dir / "tile_1_0.tif", np.array([[20.0]], dtype=np.float32), from_origin(1, 1, 1, 1))
    write_manifest(manifest_path)

    return dem_path, tiles_dir, manifest_path


def test_combined_mesh_offsets_tiles_from_manifest(tmp_path: Path) -> None:
    dem_path, tiles_dir, manifest_path = make_viewer_inputs(tmp_path)

    terrain = build_combined_terrain_mesh(dem_path, tiles_dir, manifest_path)

    assert len(terrain.vertices) == 8
    assert len(terrain.faces) == 4
    assert float(np.min(terrain.vertices[:, 0])) == 0.0
    assert float(np.max(terrain.vertices[:, 0])) == 20.0
    assert float(np.min(terrain.vertices[:, 1])) == 0.0
    assert float(np.max(terrain.vertices[:, 1])) == 10.0


def test_generate_viewer_writes_glb_and_html(tmp_path: Path) -> None:
    dem_path, tiles_dir, manifest_path = make_viewer_inputs(tmp_path)
    viewer_dir = tmp_path / "viewer"

    info = generate_viewer(dem_path, tiles_dir, manifest_path, viewer_dir)

    assert info["glb_path"] == viewer_dir / "terrain.glb"
    assert info["html_path"] == viewer_dir / "index.html"
    assert info["vertex_count"] == 8
    assert info["face_count"] == 4
    assert (viewer_dir / "terrain.glb").exists()
    html = (viewer_dir / "index.html").read_text()
    assert "terrain.glb" in html
    assert 'type="importmap"' in html


def test_viewer_cli_help_loads() -> None:
    result = CliRunner().invoke(viewer_cli, ["--help"])

    assert result.exit_code == 0
    assert "--world-name" in result.output
    assert "--output-dir" in result.output
    assert "--open" in result.output
