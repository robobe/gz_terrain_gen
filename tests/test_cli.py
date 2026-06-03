from gz_terrain_gen.cli import build_parser, default_paths
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR


def test_cli_help_loads() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "gz-terrain-gen" in help_text
    assert "download" in help_text
    assert "gazebo" in help_text


def test_default_paths_resolve_under_outputs() -> None:
    paths = default_paths(DEFAULT_OUTPUT_DIR)
    assert paths["dem"] == DEFAULT_OUTPUT_DIR / "dem_1km.tif"
    assert paths["tiles"] == DEFAULT_OUTPUT_DIR / "tiles"
    assert paths["manifest"] == DEFAULT_OUTPUT_DIR / "tiles" / "tiles.csv"
    assert paths["mesh"] == DEFAULT_OUTPUT_DIR / "mesh"
    assert paths["gz"] == DEFAULT_OUTPUT_DIR / "gz"
