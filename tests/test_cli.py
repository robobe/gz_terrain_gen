from pathlib import Path

import pytest
from click.testing import CliRunner

from gz_terrain_gen.cli import DEFAULT_WORLD_NAME, cli, default_paths
from gz_terrain_gen.main import main
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR
from gz_terrain_gen.paths import validate_world_name


def test_cli_help_loads_without_subcommands() -> None:
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "--log-level" in result.output
    assert "--world-name" in result.output
    assert "--center-lat" in result.output
    assert "--center-lon" in result.output
    assert "--size-km" in result.output
    assert "--tile-m" in result.output
    assert "--texture" in result.output
    assert "--output-dir" in result.output
    assert "Commands:" not in result.output


def test_default_paths_resolve_under_world_output() -> None:
    paths = default_paths(DEFAULT_OUTPUT_DIR, "demo")
    assert paths["world"] == DEFAULT_OUTPUT_DIR / "demo"
    assert paths["metadata"] == DEFAULT_OUTPUT_DIR / "demo" / "metadata.json"
    assert paths["dem"] == DEFAULT_OUTPUT_DIR / "demo" / "dem.tif"
    assert paths["tiles"] == DEFAULT_OUTPUT_DIR / "demo" / "tiles"
    assert paths["manifest"] == DEFAULT_OUTPUT_DIR / "demo" / "tiles" / "tiles.csv"
    assert paths["mesh"] == DEFAULT_OUTPUT_DIR / "demo" / "mesh"
    assert paths["gz"] == DEFAULT_OUTPUT_DIR / "demo" / "gz"


def test_validate_world_name_accepts_expected_names() -> None:
    assert validate_world_name("demo_world") == "demo_world"
    assert validate_world_name("world-1") == "world-1"


@pytest.mark.parametrize("world_name", ["../x", ".hidden", "bad/name", "bad name"])
def test_validate_world_name_rejects_unsafe_names(world_name: str) -> None:
    with pytest.raises(ValueError):
        validate_world_name(world_name)


def test_world_name_defaults_to_terrain_world(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured = {}

    def fake_run_pipeline(world_name, output_dir, center_lat, center_lon, size_km, tile_m, texture):
        captured["world_name"] = world_name
        captured["output_dir"] = output_dir
        return default_paths(output_dir, world_name)

    monkeypatch.setattr("gz_terrain_gen.cli.run_pipeline", fake_run_pipeline)

    result = CliRunner().invoke(cli, ["--output-dir", str(tmp_path)])

    assert result.exit_code == 0
    assert captured["world_name"] == DEFAULT_WORLD_NAME
    assert captured["output_dir"] == tmp_path


def test_cli_rejects_invalid_world_name() -> None:
    result = CliRunner().invoke(cli, ["--world-name", "bad/name"])

    assert result.exit_code != 0
    assert "world name must match" in result.output


def test_existing_world_folder_decline_aborts_before_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    world_dir = tmp_path / "demo"
    marker = world_dir / "marker.txt"
    world_dir.mkdir()
    marker.write_text("keep")
    called = False

    def fake_run_pipeline(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("gz_terrain_gen.cli.run_pipeline", fake_run_pipeline)

    result = CliRunner().invoke(
        cli,
        ["--world-name", "demo", "--output-dir", str(tmp_path)],
        input="n\n",
    )

    assert result.exit_code != 0
    assert not called
    assert marker.exists()


def test_existing_world_folder_confirm_removes_before_pipeline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    world_dir = tmp_path / "demo"
    marker = world_dir / "marker.txt"
    world_dir.mkdir()
    marker.write_text("remove")
    captured = {}

    def fake_run_pipeline(world_name, output_dir, center_lat, center_lon, size_km, tile_m, texture):
        captured["world_exists"] = (output_dir / world_name).exists()
        return default_paths(output_dir, world_name)

    monkeypatch.setattr("gz_terrain_gen.cli.run_pipeline", fake_run_pipeline)

    result = CliRunner().invoke(
        cli,
        ["--world-name", "demo", "--output-dir", str(tmp_path)],
        input="y\n",
    )

    assert result.exit_code == 0
    assert captured["world_exists"] is False
    assert not marker.exists()


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
