import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

from gz_terrain_gen.metadata import dem_metadata, requested_area_metadata, update_metadata


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
    assert metadata["dem"]["width_px"] == 2
    assert metadata["dem"]["height_px"] == 2
    assert metadata["dem"]["elevation"]["minimum_m"] == 10.0
    assert metadata["dem"]["elevation"]["maximum_m"] == 40.0
    assert metadata["dem"]["elevation"]["mean_m"] == 25.0
