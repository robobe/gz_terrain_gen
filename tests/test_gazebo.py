"""Tests for Gazebo model and world generation."""

import ast
from pathlib import Path

from gz_terrain_gen.gazebo import (
    dae_center_elevation,
    model_name,
    probe_pose,
    render_gui,
    single_world_sdf,
    travel_script,
    world_sdf,
    write_probe_model,
)

GAZEBO_MODULE = Path("src/gz_terrain_gen/gazebo.py")


def write_dae(path: Path, positions: str) -> None:
    path.write_text(
        f"""<?xml version="1.0"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema">
  <library_geometries>
    <geometry id="tile_0_0">
      <mesh>
        <source id="tile_0_0-positions">
          <float_array id="tile_0_0-positions-array" count="{len(positions.split())}">{positions}</float_array>
        </source>
      </mesh>
    </geometry>
  </library_geometries>
</COLLADA>
"""
    )


def test_model_name_prefixes_tile_stem() -> None:
    assert model_name("tile_0_0") == "terrain_tile_0_0"


def test_gazebo_stable_identifiers_are_defined_once_as_constants() -> None:
    tree = ast.parse(GAZEBO_MODULE.read_text(encoding="utf-8"))
    string_values = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]

    stable_identifiers = [
        "model.config",
        "model.sdf",
        "models",
        "meshes",
        "materials",
        "textures",
        "soil.jpg",
        ".dae",
        "levels_terrain.sdf",
        "single_tile_terrain.sdf",
        "travel_levels.sh",
        "README.md",
        "level_probe",
        "model://",
        "gazebo_center_x_m",
        "gazebo_center_y_m",
        "gazebo_corner_x_m",
        "gazebo_corner_y_m",
    ]

    for identifier in stable_identifiers:
        assert string_values.count(identifier) == 1


def test_world_sdf_contains_expected_world_and_model_names() -> None:
    tiles = [
        {
            "file": "tile_0_0.tif",
            "tile_x": "0",
            "tile_y": "0",
            "gazebo_corner_x_m": "0",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "100",
            "gazebo_center_y_m": "100",
        }
    ]

    sdf = world_sdf(tiles, "demo_world")

    assert '<world name="demo_world">' in sdf
    assert "<name>terrain_tile_0_0</name>" in sdf
    assert '<level name="level_tile_0_0">' in sdf
    assert "<ref>terrain_tile_0_0</ref>" in sdf


def test_rendered_gui_replaces_minimal_scene_camera_pose() -> None:
    gui = render_gui("100.000 100.000 250.000 0 1.5708 0")

    assert "MinimalScene" in gui
    assert "<camera_pose>100.000 100.000 250.000 0 1.5708 0</camera_pose>" in gui
    assert "<camera_pose>-6 0 6 0 0.5 0</camera_pose>" not in gui


def test_dae_center_elevation_returns_exact_center_z(tmp_path: Path) -> None:
    dae = tmp_path / "tile_0_0.dae"
    write_dae(dae, "-1 -1 10 0 0 42 1 1 30")

    assert dae_center_elevation(dae) == 42


def test_dae_center_elevation_falls_back_to_nearest_vertex(tmp_path: Path) -> None:
    dae = tmp_path / "tile_0_0.dae"
    write_dae(dae, "-10 -10 10 2 1 22 5 5 50")

    assert dae_center_elevation(dae) == 22


def test_probe_pose_uses_first_tile_center_and_30_meter_clearance() -> None:
    tiles = [
        {
            "gazebo_corner_x_m": "0",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "100",
            "gazebo_center_y_m": "100",
        }
    ]

    pose = probe_pose(tiles, 40.0)

    assert pose == (100.0, 100.0, 70.0)


def test_write_probe_model_has_zero_internal_pose(tmp_path: Path) -> None:
    write_probe_model(tmp_path)

    assert "<pose>0 0 0 0 0 0</pose>" in (tmp_path / "level_probe" / "model.sdf").read_text()


def test_world_sdf_contains_gui_before_sun_light_and_rendering_plugin() -> None:
    tiles = [
        {
            "file": "tile_0_0.tif",
            "tile_x": "0",
            "tile_y": "0",
            "gazebo_corner_x_m": "0",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "100",
            "gazebo_center_y_m": "100",
        }
    ]

    sdf = world_sdf(tiles, "demo_world", 40.0, 1500.0)

    assert '<plugin filename="gz-sim-rendering-system" name="gz::sim::systems::Rendering"/>' in sdf
    assert "MinimalScene" in sdf
    assert "<camera_pose>100.000 100.000 140.000 0 1.5708 0</camera_pose>" in sdf
    assert "<pose>100.000 100.000 70.000 0 0 0</pose>" in sdf
    assert "<size>200.000 200.000 1500.000</size>" in sdf
    assert sdf.index("<gui") < sdf.index('<light name="sun"')


def test_single_world_sdf_contains_gui_before_sun_light() -> None:
    tiles = [
        {
            "gazebo_corner_x_m": "0",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "100",
            "gazebo_center_y_m": "100",
        }
    ]

    sdf = single_world_sdf(tiles, 40.0)

    assert "MinimalScene" in sdf
    assert "<camera_pose>100.000 100.000 140.000 0 1.5708 0</camera_pose>" in sdf
    assert "<pose>100.000 100.000 0 0 0 0</pose>" in sdf
    assert sdf.index("<gui") < sdf.index('<light name="sun"')


def test_travel_script_defaults_to_world_name() -> None:
    script = travel_script(
        [
            {
                "tile_x": "0",
                "tile_y": "0",
                "gazebo_center_x_m": "100",
                "gazebo_center_y_m": "100",
            }
        ],
        "demo_world",
        70.0,
    )

    assert 'WORLD="${1:-demo_world}"' in script
    assert 'Z="${Z:-70.000}"' in script
