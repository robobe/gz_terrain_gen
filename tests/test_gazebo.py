from gz_terrain_gen.gazebo import camera_pose, model_name, render_gui, single_world_sdf, travel_script, world_sdf


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


def test_rendered_gui_replaces_minimal_scene_camera_pose() -> None:
    gui = render_gui("100.000 100.000 250.000 0 1.5708 0")

    assert "MinimalScene" in gui
    assert "<camera_pose>100.000 100.000 250.000 0 1.5708 0</camera_pose>" in gui
    assert "<camera_pose>-6 0 6 0 0.5 0</camera_pose>" not in gui


def test_camera_pose_uses_first_tile_and_auto_height() -> None:
    tiles = [
        {
            "gazebo_corner_x_m": "0",
            "gazebo_corner_y_m": "0",
            "gazebo_center_x_m": "100",
            "gazebo_center_y_m": "100",
        }
    ]

    pose = camera_pose(tiles, 40.0)

    assert pose == "100.000 100.000 190.000 0 1.5708 0"


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

    sdf = world_sdf(tiles, "demo_world", 40.0)

    assert '<plugin filename="gz-sim-rendering-system" name="gz::sim::systems::Rendering"/>' in sdf
    assert "MinimalScene" in sdf
    assert "<camera_pose>100.000 100.000 190.000 0 1.5708 0</camera_pose>" in sdf
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
    assert "<camera_pose>100.000 100.000 190.000 0 1.5708 0</camera_pose>" in sdf
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
    )

    assert 'WORLD="${1:-demo_world}"' in script
