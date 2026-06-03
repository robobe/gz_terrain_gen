import pytest
from click.testing import CliRunner

from gz_terrain_gen.cli import default_paths, main
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR
from gz_terrain_gen.paths import validate_world_name


def test_cli_help_loads() -> None:
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "--log-level" in result.output
    assert "download" in result.output
    assert "gazebo" in result.output


def test_default_paths_resolve_under_world_output() -> None:
    paths = default_paths(DEFAULT_OUTPUT_DIR, "demo")
    assert paths["world"] == DEFAULT_OUTPUT_DIR / "demo"
    assert paths["metadata"] == DEFAULT_OUTPUT_DIR / "demo" / "metadata.json"
    assert paths["dem"] == DEFAULT_OUTPUT_DIR / "demo" / "dem_1km.tif"
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


def test_cli_requires_world_name() -> None:
    result = CliRunner().invoke(main, ["split"])

    assert result.exit_code != 0
    assert "Missing option '--world-name'" in result.output


def test_cli_rejects_invalid_world_name() -> None:
    result = CliRunner().invoke(main, ["split", "--world-name", "bad/name"])

    assert result.exit_code != 0
    assert "world name must match" in result.output


def test_all_help_loads() -> None:
    result = CliRunner().invoke(main, ["all", "--help"])

    assert result.exit_code == 0
    assert "--world-name" in result.output
    assert "--center-lat" in result.output


def test_split_help_loads_with_world_name() -> None:
    result = CliRunner().invoke(main, ["split", "--world-name", "test_world", "--help"])

    assert result.exit_code == 0
    assert "--tile-m" in result.output


def test_log_level_option_works_before_subcommand() -> None:
    result = CliRunner().invoke(main, ["--log-level", "DEBUG", "split", "--world-name", "test_world", "--help"])

    assert result.exit_code == 0
    assert "--tile-m" in result.output


def test_invalid_log_level_fails() -> None:
    result = CliRunner().invoke(main, ["--log-level", "LOUD", "split", "--world-name", "test_world"])

    assert result.exit_code != 0
    assert "Invalid value for '--log-level'" in result.output
