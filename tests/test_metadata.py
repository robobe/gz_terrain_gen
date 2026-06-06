import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

from gz_terrain_gen.metadata import (
    ElevationStats,
    MeshMetadata,
    MetadataDocument,
    MetadataUpdate,
    RequestMetadata,
    elevation_stats,
    mesh_metadata,
    read_metadata,
    requested_area_metadata,
    tile_metadata,
    update_metadata,
)


def write_test_dem(path, data) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=from_origin(34.0, 31.0, 0.1, 0.1),
    ) as dst:
        dst.write(data, 1)


def test_metadata_writes_expected_keys_and_elevation_stats(tmp_path) -> None:
    dem_path = tmp_path / "dem.tif"
    metadata_path = tmp_path / "metadata.json"
    data = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)
    write_test_dem(dem_path, data)

    update_metadata(
        metadata_path,
        "demo_world",
        MetadataUpdate(
            request=requested_area_metadata(30.9, 34.4, 1.0, elevation_stats(dem_path)),
            tiles=tile_metadata(2, 200),
            mesh=mesh_metadata(2, 10.0),
        ),
    )

    payload = json.loads(metadata_path.read_text())
    document = read_metadata(metadata_path)

    assert isinstance(document, MetadataDocument)
    assert isinstance(document.request, RequestMetadata)
    assert payload["schema_version"] == 1
    assert payload["world_name"] == "demo_world"
    assert payload["request"]["center_lat"] == 30.9
    assert payload["request"]["center_lon"] == 34.4
    assert payload["request"]["size_km"] == 1.0
    assert payload["request"]["elevation"]["minimum_m"] == 10.0
    assert payload["request"]["elevation"]["maximum_m"] == 40.0
    assert payload["request"]["elevation"]["mean_m"] == 25.0
    assert payload["tiles"]["tile_m"] == 200
    assert payload["tiles"]["count"] == 2
    assert payload["mesh"]["count"] == 2
    assert payload["mesh"]["normalized_to_gazebo_z_zero"] is True
    assert payload["mesh"]["z_offset_m"] == 10.0
    assert "d" + "em" not in payload
    assert "gaze" + "bo" not in payload
    assert "view" + "er" not in payload


def test_elevation_stats_handles_empty_valid_values(tmp_path) -> None:
    dem_path = tmp_path / "dem.tif"
    data = np.array([[-9999.0, -9999.0]], dtype=np.float32)
    with rasterio.open(
        dem_path,
        "w",
        driver="GTiff",
        height=1,
        width=2,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=from_origin(34.0, 31.0, 0.1, 0.1),
        nodata=-9999.0,
    ) as dst:
        dst.write(data, 1)

    stats = elevation_stats(dem_path)

    assert stats == ElevationStats(minimum_m=None, maximum_m=None, mean_m=None)


def test_mesh_metadata_records_z_normalization() -> None:
    metadata = mesh_metadata(3, 42.5)

    assert isinstance(metadata, MeshMetadata)
    assert metadata.count == 3
    assert metadata.normalized_to_gazebo_z_zero is True
    assert metadata.z_offset_m == 42.5


def test_update_metadata_preserves_unknown_top_level_keys_and_created_at(tmp_path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "world_name": "old_world",
                "created_at": "2026-01-01T00:00:00+00:00",
                "custom": {"keep": True},
            }
        )
    )

    document = update_metadata(
        metadata_path,
        "demo_world",
        MetadataUpdate(tiles=tile_metadata(2, 200)),
    )
    payload = json.loads(metadata_path.read_text())

    assert document.created_at == "2026-01-01T00:00:00+00:00"
    assert document.updated_at is not None
    assert document.extra == {"custom": {"keep": True}}
    assert payload["custom"] == {"keep": True}
    assert payload["created_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["world_name"] == "demo_world"


def test_unknown_sections_are_preserved_as_extra(tmp_path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "world_name": "demo_world",
                "custom_section": {"legacy": True},
            }
        )
    )

    document = read_metadata(metadata_path)

    assert document.extra == {"custom_section": {"legacy": True}}
