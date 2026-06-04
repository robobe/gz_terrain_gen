import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

from gz_terrain_gen.gazebo import GazeboGenerationResult
from gz_terrain_gen.metadata import (
    dem_metadata,
    gazebo_metadata,
    mesh_metadata,
    requested_area_metadata,
    update_metadata,
    viewer_metadata,
)
from gz_terrain_gen.viewer import ViewerGenerationResult


def test_metadata_writes_expected_keys_and_elevation_stats(tmp_path) -> None:
    dem_path = tmp_path / "dem.tif"
    metadata_path = tmp_path / "metadata.json"
    data = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)

    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        height=2,
        width=2,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=from_origin(34.0, 31.0, 0.1, 0.1),
    ) as dst:
        dst.write(data, 1)

    update_metadata(
        metadata_path,
        "demo_world",
        {
            "request": requested_area_metadata(30.9, 34.4, 1.0, "COP30"),
            "dem": dem_metadata(dem_path),
        },
    )

    metadata = json.loads(metadata_path.read_text())

    assert metadata["schema_version"] == 1
    assert metadata["world_name"] == "demo_world"
    assert metadata["request"]["center_lat"] == 30.9
    assert metadata["request"]["source"] == "opentopography"
    assert metadata["dem"]["width_px"] == 2
    assert metadata["dem"]["height_px"] == 2
    assert metadata["dem"]["elevation"]["minimum_m"] == 10.0
    assert metadata["dem"]["elevation"]["maximum_m"] == 40.0
    assert metadata["dem"]["elevation"]["mean_m"] == 25.0


def test_viewer_metadata_contains_expected_paths(tmp_path) -> None:
    viewer_dir = tmp_path / "viewer"
    metadata = viewer_metadata(
        ViewerGenerationResult(
            viewer_dir=viewer_dir,
            glb_path=viewer_dir / "terrain.glb",
            html_path=viewer_dir / "index.html",
            vertex_count=8,
            face_count=4,
        )
    )

    assert metadata["viewer_dir"] == str(viewer_dir)
    assert metadata["glb_path"] == str(viewer_dir / "terrain.glb")
    assert metadata["html_path"] == str(viewer_dir / "index.html")
    assert metadata["vertex_count"] == 8
    assert metadata["face_count"] == 4


def test_mesh_metadata_records_z_normalization(tmp_path) -> None:
    metadata = mesh_metadata(3, tmp_path / "mesh", 42.5)

    assert metadata["count"] == 3
    assert metadata["mesh_dir"] == str(tmp_path / "mesh")
    assert metadata["normalized_to_gazebo_z_zero"] is True
    assert metadata["z_offset_m"] == 42.5


def test_gazebo_metadata_records_probe_camera_and_level_z_size(tmp_path) -> None:
    metadata = gazebo_metadata(
        2,
        tmp_path / "gz",
        GazeboGenerationResult(
            model_count=2,
            probe_pose={"x": 100.0, "y": 100.0, "z": 70.0},
            gui_camera_pose="100.000 100.000 140.000 0 1.5708 0",
            level_z_size_m=1500.0,
        ),
    )

    assert metadata["model_count"] == 2
    assert metadata["probe_pose"] == {"x": 100.0, "y": 100.0, "z": 70.0}
    assert metadata["gui_camera_pose"] == "100.000 100.000 140.000 0 1.5708 0"
    assert metadata["level_z_size_m"] == 1500.0
