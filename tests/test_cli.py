from pathlib import Path

import numpy as np
import pytest
import rasterio
import click
from click.testing import CliRunner
from rasterio.transform import from_origin

from gz_terrain_gen.cli import DEFAULT_WORLD_NAME, TerrainGenerationConfig, cli, default_paths
from gz_terrain_gen.gazebo import GazeboGenerationResult
from gz_terrain_gen.main import (
    format_completion_summary,
    format_start_banner,
    generate_mesh_stage,
    main,
    prepare_dem,
    print_pipeline_completion,
    split_tiles_stage,
)
from gz_terrain_gen.metadata import (
    ElevationStats,
    GeoBounds,
    MeshMetadata,
    MetadataDocument,
    RequestMetadata,
    TileMetadata,
)
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, WorldPaths, validate_world_name
from gz_terrain_gen.viewer import ViewerGenerationResult


def test_cli_help_loads_without_subcommands() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--log-level" in result.output
    assert "--world-name" in result.output
    assert "--center-lat" in result.output
    assert "--center-lon" in result.output
    assert "--size-km" in result.output
    assert "--tile-m" in result.output
    assert "--level-z-size-m" in result.output
    assert "--texture" in result.output
    assert "--output-dir" in result.output
    assert "--dem-file" in result.output
    assert "Commands:" not in result.output


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


def test_default_paths_resolve_under_world_output() -> None:
    paths = default_paths(DEFAULT_OUTPUT_DIR, "demo")
    viewer_dir_name = "view" + "er"
    assert isinstance(paths, WorldPaths)
    assert paths.world == DEFAULT_OUTPUT_DIR / "demo"
    assert paths.metadata == DEFAULT_OUTPUT_DIR / "demo" / "metadata.json"
    assert paths.dem == DEFAULT_OUTPUT_DIR / "demo" / "dem.tif"
    assert paths.tiles == DEFAULT_OUTPUT_DIR / "demo" / "tiles"
    assert paths.manifest == DEFAULT_OUTPUT_DIR / "demo" / "tiles" / "tiles.csv"
    assert paths.mesh == DEFAULT_OUTPUT_DIR / "demo" / "mesh"
    assert paths.gz == DEFAULT_OUTPUT_DIR / "demo" / "gz"
    assert paths.viewer == DEFAULT_OUTPUT_DIR / "demo" / viewer_dir_name


def test_start_banner_contains_version_world_and_output(tmp_path: Path) -> None:
    banner = format_start_banner("0.1.0", "demo_world", tmp_path / "demo_world")

    assert "GZ Terrain Generator" in banner
    assert "Version: 0.1.0" in banner
    assert "World: demo_world" in banner
    assert f"Output: {tmp_path / 'demo_world'}" in banner


def test_completion_summary_contains_generated_result(tmp_path: Path) -> None:
    metadata_path = tmp_path / "demo_world" / "metadata.json"
    metadata = MetadataDocument(
        world_name="demo_world",
        request=RequestMetadata(
            center_lat=30.611505,
            center_lon=34.808504,
            size_km=2.0,
            bounds=GeoBounds(west=34.7, south=30.5, east=34.9, north=30.7),
            elevation=ElevationStats(minimum_m=100.0, maximum_m=240.25, mean_m=150.5),
        ),
        mesh=MeshMetadata(
            count=4,
            normalized_to_gazebo_z_zero=True,
            z_offset_m=100.0,
        ),
        tiles=TileMetadata(
            count=4,
            tile_m=200,
        ),
    )

    summary = format_completion_summary(metadata, metadata_path)

    assert "Generation Summary" in summary
    assert "World: demo_world" in summary
    assert "Area: 2.000 km x 2.000 km" in summary
    assert "Center: 30.611505, 34.808504" in summary
    assert "Bounds: west=34.700000, south=30.500000, east=34.900000, north=30.700000" in summary
    assert "Elevation: min=100.000 m, max=240.250 m, mean=150.500 m" in summary
    assert "Z normalization: enabled, offset=100.000 m" in summary
    assert "Tiles: 4 at 200 m" in summary
    assert "Meshes: 4" in summary
    assert f"Metadata: {metadata_path}" in summary


def test_validate_world_name_accepts_expected_names() -> None:
    assert validate_world_name("demo_world") == "demo_world"
    assert validate_world_name("world-1") == "world-1"


@pytest.mark.parametrize("world_name", ["../x", ".hidden", "bad/name", "bad name"])
def test_validate_world_name_rejects_unsafe_names(world_name: str) -> None:
    with pytest.raises(ValueError):
        validate_world_name(world_name)


def test_cli_returns_config_with_default_world_name(tmp_path: Path) -> None:
    result = CliRunner().invoke(cli, ["--output-dir", str(tmp_path)], standalone_mode=False)

    assert result.exit_code == 0
    assert isinstance(result.return_value, TerrainGenerationConfig)
    assert result.return_value.world_name == DEFAULT_WORLD_NAME
    assert result.return_value.output_dir == tmp_path
    assert result.return_value.level_z_size_m == 1500
    assert result.return_value.dem_file is None


def test_cli_rejects_invalid_world_name() -> None:
    result = CliRunner().invoke(cli, ["--world-name", "bad/name"])

    assert result.exit_code != 0
    assert "world name must match" in result.output


def test_main_uses_parsed_config_and_prints_start_banner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    captured = {}

    def fake_run_pipeline(config):
        captured["config"] = config
        return default_paths(config.output_dir, config.world_name)

    monkeypatch.setattr("gz_terrain_gen.main.run_pipeline", fake_run_pipeline)

    main(["--world-name", "demo", "--output-dir", str(tmp_path)])

    assert captured["config"].world_name == "demo"
    assert captured["config"].output_dir == tmp_path
    assert captured["config"].level_z_size_m == 1500
    output = capsys.readouterr().out
    assert "GZ Terrain Generator" in output
    assert "Version: 0.1.0" in output
    assert f"Output: {tmp_path / 'demo'}" in output


def test_existing_world_folder_decline_aborts_before_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    world_dir = tmp_path / "demo"
    marker = world_dir / "marker.txt"
    world_dir.mkdir()
    marker.write_text("keep")
    called = False

    def fake_run_pipeline(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("gz_terrain_gen.main.run_pipeline", fake_run_pipeline)

    @click.command()
    def command():
        main(["--world-name", "demo", "--output-dir", str(tmp_path)])

    result = CliRunner().invoke(command, input="n\n")

    assert result.exit_code != 0
    assert not called
    assert marker.exists()


def test_existing_world_folder_confirm_removes_before_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    world_dir = tmp_path / "demo"
    marker = world_dir / "marker.txt"
    world_dir.mkdir()
    marker.write_text("remove")
    captured = {}

    def fake_run_pipeline(config):
        captured["world_exists"] = (config.output_dir / config.world_name).exists()
        return default_paths(config.output_dir, config.world_name)

    monkeypatch.setattr("gz_terrain_gen.main.run_pipeline", fake_run_pipeline)

    @click.command()
    def command():
        main(["--world-name", "demo", "--output-dir", str(tmp_path)])

    result = CliRunner().invoke(command, input="y\n")

    assert result.exit_code == 0
    assert captured["world_exists"] is False
    assert not marker.exists()


def test_cli_parses_existing_dem_file(tmp_path: Path) -> None:
    dem_path = tmp_path / "input.tif"
    write_test_dem(dem_path)

    result = CliRunner().invoke(
        cli,
        ["--output-dir", str(tmp_path / "outputs"), "--dem-file", str(dem_path)],
        standalone_mode=False,
    )

    assert result.exit_code == 0
    assert result.return_value.dem_file == dem_path
    assert result.return_value.level_z_size_m == 1500


def test_prepare_dem_local_file_copies_dem_and_returns_local_metadata(tmp_path: Path) -> None:
    dem_path = tmp_path / "source.tif"
    output_dir = tmp_path / "outputs"
    write_test_dem(dem_path)
    config = TerrainGenerationConfig(
        log_level="INFO",
        world_name="demo",
        output_dir=output_dir,
        center_lat=30.0,
        center_lon=34.0,
        size_km=1.0,
        tile_m=200,
        level_z_size_m=1500,
        texture=tmp_path / "texture.jpg",
        dem_file=dem_path,
    )
    paths = default_paths(output_dir, "demo")

    result = prepare_dem(config, paths)

    assert paths.dem.exists()
    assert paths.dem.read_bytes() == dem_path.read_bytes()
    assert result.request_metadata.elevation.minimum_m == 10.0
    assert result.request_metadata.elevation.maximum_m == 40.0


def test_split_tiles_stage_returns_tile_count_and_manifest(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = TerrainGenerationConfig(
        log_level="INFO",
        world_name="demo",
        output_dir=tmp_path / "outputs",
        center_lat=30.0,
        center_lon=34.0,
        size_km=1.0,
        tile_m=200,
        level_z_size_m=1500,
        texture=tmp_path / "texture.jpg",
        dem_file=None,
    )
    paths = default_paths(config.output_dir, config.world_name)
    monkeypatch.setattr("gz_terrain_gen.main.split_dem", lambda dem, tiles, tile_m: (3, tiles / "tiles.csv"))

    result = split_tiles_stage(config, paths)

    assert result.tile_count == 3
    assert result.manifest == paths.tiles / "tiles.csv"


def test_generate_mesh_stage_returns_mesh_count_and_z_offset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config = TerrainGenerationConfig(
        log_level="INFO",
        world_name="demo",
        output_dir=tmp_path / "outputs",
        center_lat=30.0,
        center_lon=34.0,
        size_km=1.0,
        tile_m=200,
        level_z_size_m=1500,
        texture=tmp_path / "texture.jpg",
        dem_file=None,
    )
    paths = default_paths(config.output_dir, config.world_name)
    monkeypatch.setattr("gz_terrain_gen.main.generate_meshes", lambda source_dem, tiles_dir, manifest_path, mesh_dir: 4)
    monkeypatch.setattr("gz_terrain_gen.main.open_dem", lambda dem: (None, None, None, None, 42.5))

    result = generate_mesh_stage(config, paths)

    assert result.mesh_count == 4
    assert result.z_offset_m == 42.5


def test_print_pipeline_completion_outputs_viewer_command_metadata_and_summary(tmp_path: Path, capsys) -> None:
    config = TerrainGenerationConfig(
        log_level="INFO",
        world_name="demo",
        output_dir=tmp_path / "outputs",
        center_lat=30.0,
        center_lon=34.0,
        size_km=1.0,
        tile_m=200,
        level_z_size_m=1500,
        texture=tmp_path / "texture.jpg",
        dem_file=None,
    )
    paths = default_paths(config.output_dir, config.world_name)
    metadata = MetadataDocument(
        world_name="demo",
        request=RequestMetadata(
            center_lat=30.0,
            center_lon=34.0,
            size_km=1.0,
            bounds=GeoBounds(west=0.0, south=0.0, east=0.0, north=0.0),
            elevation=ElevationStats(minimum_m=None, maximum_m=None, mean_m=None),
        ),
    )

    print_pipeline_completion(config, paths, metadata)

    output = capsys.readouterr().out
    assert "serve viewer: uv run gz-terrain-gen-viewer --world-name demo" in output
    assert f"metadata: {paths.metadata}" in output
    assert "Generation Summary" in output


def test_run_pipeline_with_dem_file_skips_download_and_copies_dem(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    from gz_terrain_gen.main import run_pipeline

    dem_path = tmp_path / "source.tif"
    output_dir = tmp_path / "outputs"
    write_test_dem(dem_path)

    def fail_download(*args, **kwargs):
        raise AssertionError("download_dem should not be called")

    monkeypatch.setattr("gz_terrain_gen.main.download_dem", fail_download)
    monkeypatch.setattr("gz_terrain_gen.main.split_dem", lambda dem, tiles, tile_m: (0, tiles / "tiles.csv"))
    monkeypatch.setattr("gz_terrain_gen.main.generate_meshes", lambda source_dem, tiles_dir, manifest_path, mesh_dir: 0)
    monkeypatch.setattr(
        "gz_terrain_gen.main.generate_gazebo_worlds",
        lambda manifest, mesh, texture, gz, world, level_z_size_m: GazeboGenerationResult(
            model_count=0,
            probe_pose={"x": 0.0, "y": 0.0, "z": 30.0},
            gui_camera_pose="0.000 0.000 100.000 0 1.5708 0",
            level_z_size_m=level_z_size_m,
        ),
    )
    monkeypatch.setattr(
        "gz_terrain_gen.main.generate_viewer",
        lambda source_dem, tiles_dir, manifest_path, viewer_dir: ViewerGenerationResult(
            viewer_dir=viewer_dir,
            glb_path=viewer_dir / "terrain.glb",
            html_path=viewer_dir / "index.html",
            vertex_count=0,
            face_count=0,
        ),
    )

    paths = run_pipeline(
        TerrainGenerationConfig(
            log_level="INFO",
            world_name="demo",
            output_dir=output_dir,
            center_lat=30.0,
            center_lon=34.0,
            size_km=1.0,
            tile_m=200,
            level_z_size_m=1500,
            texture=tmp_path / "texture.jpg",
            dem_file=dem_path,
        )
    )

    assert paths.dem.exists()
    assert paths.dem.read_bytes() == dem_path.read_bytes()
    metadata = paths.metadata.read_text()
    assert '"minimum_m": 10.0' in metadata
    assert f'"{"d" + "em"}"' not in metadata
    assert f'"{"gaze" + "bo"}"' not in metadata
    assert f'"{"view" + "er"}"' not in metadata


def test_log_level_option_works() -> None:
    result = CliRunner().invoke(cli, ["--log-level", "DEBUG", "--help"])

    assert result.exit_code == 0
    assert "--tile-m" in result.output


def test_invalid_log_level_fails() -> None:
    result = CliRunner().invoke(cli, ["--log-level", "LOUD"])

    assert result.exit_code != 0
    assert "Invalid value for '--log-level'" in result.output


def test_package_main_imports_and_is_callable() -> None:
    assert callable(main)
