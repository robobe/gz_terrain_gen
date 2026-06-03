import pytest

from gz_terrain_gen.cli import build_parser, default_paths
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR
from gz_terrain_gen.paths import validate_world_name


def test_cli_help_loads() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "gz-terrain-gen" in help_text
    assert "download" in help_text
    assert "gazebo" in help_text


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
    parser = build_parser()

    with pytest.raises(SystemExit):
        parser.parse_args(["split"])
