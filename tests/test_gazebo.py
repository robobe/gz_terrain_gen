from gz_terrain_gen.gazebo import model_name, travel_script, world_sdf


def test_model_name_prefixes_tile_stem() -> None:
    assert model_name("tile_0_0") == "terrain_tile_0_0"


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
    )

    assert 'WORLD="${1:-demo_world}"' in script
