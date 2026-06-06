from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gz_terrain_gen.cli import TerrainGenerationConfig
from gz_terrain_gen.dem_source import DemSourceResult, LocalFileDemSource, OpenTopographyDemSource
from gz_terrain_gen.main import dem_source_from_config


def write_test_dem(path: Path) -> None:
    data = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)
    with rasterio.open(
        path,
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


@pytest.fixture
def demo_config(tmp_path: Path):
    def make_config(**overrides):
        values = {
            "log_level": "INFO",
            "world_name": "demo",
            "output_dir": tmp_path / "outputs",
            "center_lat": 30.0,
            "center_lon": 34.0,
            "size_km": 1.0,
            "tile_m": 200,
            "level_z_size_m": 1500,
            "texture": tmp_path / "texture.jpg",
            "dem_file": None,
        }
        values.update(overrides)
        return TerrainGenerationConfig(**values)

    return make_config


def test_local_file_dem_source_copies_source_to_output(tmp_path: Path) -> None:
    source_path = tmp_path / "source.tif"
    output_path = tmp_path / "world" / "dem.tif"
    write_test_dem(source_path)

    result = LocalFileDemSource(source_path).prepare(output_path)

    assert isinstance(result, DemSourceResult)
    assert result.source_name == "local_file"
    assert result.path == output_path
    assert output_path.exists()
    assert output_path.read_bytes() == source_path.read_bytes()


def test_open_topography_dem_source_calls_download_dem(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def fake_download_dem(output_path, api_key, center_lat, center_lon, size_km, dem_type):
        captured["output_path"] = output_path
        captured["api_key"] = api_key
        captured["center_lat"] = center_lat
        captured["center_lon"] = center_lon
        captured["size_km"] = size_km
        captured["dem_type"] = dem_type
        return output_path

    monkeypatch.setattr("gz_terrain_gen.dem_source.download_dem", fake_download_dem)
    output_path = tmp_path / "dem.tif"
    source = OpenTopographyDemSource(
        center_lat=30.0,
        center_lon=34.0,
        size_km=1.5,
        dem_type="COP30",
        api_key="token",
    )

    result = source.prepare(output_path)

    assert result == DemSourceResult(path=output_path, source_name="opentopography")
    assert captured == {
        "output_path": output_path,
        "api_key": "token",
        "center_lat": 30.0,
        "center_lon": 34.0,
        "size_km": 1.5,
        "dem_type": "COP30",
    }


def test_dem_source_from_config_uses_local_file_source(demo_config) -> None:
    config = demo_config(dem_file=Path("input.tif"))

    source = dem_source_from_config(config)

    assert isinstance(source, LocalFileDemSource)
    assert source.source_path == Path("input.tif")


def test_dem_source_from_config_uses_open_topography_source(demo_config) -> None:
    config = demo_config(dem_file=None, center_lat=31.0, center_lon=35.0, size_km=3.0)

    source = dem_source_from_config(config)

    assert isinstance(source, OpenTopographyDemSource)
    assert source.center_lat == 31.0
    assert source.center_lon == 35.0
    assert source.size_km == 3.0
