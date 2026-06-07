"""
Generate Gazebo world and model files for DEM mesh terrain tiles.

This module converts generated Collada terrain tiles into textured Gazebo models,
writes level-aware SDF worlds, and emits helper files for previewing level loading.
"""

import csv
import shutil
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET

TEXT_ENCODING = "utf-8"
XML_TEXT_ENCODING = "unicode"
XML_DEFAULT_NAMESPACE_PREFIX = ""
COLLADA_NAMESPACE_ALIAS = "c"
COLLADA_MESH_SELECTOR = ".//c:mesh"
COLLADA_POSITION_ARRAY_SELECTOR = "c:source/c:float_array"
COLLADA_POSITION_ARRAY_ANYWHERE_SELECTOR = ".//c:source/c:float_array"
COLLADA_GEOMETRY_SELECTOR = ".//c:geometry"
COLLADA_SOURCE_SELECTOR = "c:source"
COLLADA_TRIANGLES_SELECTOR = "c:triangles"
COLLADA_TRIANGLE_INDICES_SELECTOR = "c:p"
COLLADA_NORMAL_INPUT_SELECTOR = "c:input[@semantic='NORMAL']"
COLLADA_TEXCOORD_INPUT_SELECTOR = "c:input[@semantic='TEXCOORD']"
COLLADA_ID_ATTR = "id"
COLLADA_COUNT_ATTR = "count"
COLLADA_SOURCE_TAG = "source"
COLLADA_FLOAT_ARRAY_TAG = "float_array"
COLLADA_TECHNIQUE_COMMON_TAG = "technique_common"
COLLADA_ACCESSOR_TAG = "accessor"
COLLADA_PARAM_TAG = "param"
COLLADA_INPUT_TAG = "input"
COLLADA_NORMAL_SUFFIX = "-normals"
COLLADA_ARRAY_SUFFIX = "-array"
COLLADA_UV_SUFFIX = "-uv"
COLLADA_UP_NORMAL = "0 0 1"
COLLADA_SEMANTIC_ATTR = "semantic"
COLLADA_SOURCE_ATTR = "source"
COLLADA_STRIDE_ATTR = "stride"
COLLADA_NORMAL_SEMANTIC = "NORMAL"
COLLADA_TEXCOORD_SEMANTIC = "TEXCOORD"
COLLADA_OFFSET_ATTR = "offset"
COLLADA_SET_ATTR = "set"
COLLADA_NAME_ATTR = "name"
COLLADA_TYPE_ATTR = "type"
COLLADA_FLOAT_TYPE = "float"
COLLADA_X_PARAM = "X"
COLLADA_Y_PARAM = "Y"
COLLADA_Z_PARAM = "Z"
COLLADA_S_PARAM = "S"
COLLADA_T_PARAM = "T"

TEMPLATES_DIR = "templates"
GUI_TEMPLATE_FILE = "gz_gui.xml"
MODEL_CONFIG_FILE = "model.config"
MODEL_SDF_FILE = "model.sdf"
MODELS_DIR = "models"
MESHES_DIR = "meshes"
MATERIALS_DIR = "materials"
TEXTURES_DIR = "textures"
SOIL_TEXTURE_FILE = "soil.jpg"
DAE_SUFFIX = ".dae"
LEVELS_TERRAIN_SDF = "levels_terrain.sdf"
SINGLE_TILE_TERRAIN_SDF = "single_tile_terrain.sdf"
TRAVEL_LEVELS_SCRIPT = "travel_levels.sh"
README_FILE = "README.md"

TILE_FILE_KEY = "file"
TILE_X_KEY = "tile_x"
TILE_Y_KEY = "tile_y"
GAZEBO_CENTER_X_KEY = "gazebo_center_x_m"
GAZEBO_CENTER_Y_KEY = "gazebo_center_y_m"
GAZEBO_CORNER_X_KEY = "gazebo_corner_x_m"
GAZEBO_CORNER_Y_KEY = "gazebo_corner_y_m"
RESULT_X_KEY = "x"
RESULT_Y_KEY = "y"
RESULT_Z_KEY = "z"

TERRAIN_MODEL_PREFIX = "terrain_"
LEVEL_PREFIX = "level_"
SINGLE_TILE_WORLD_NAME = "single_tile_terrain"
SINGLE_TILE_MODEL_NAME = "terrain_tile_0_0"
MODEL_URI_PREFIX = "model://"
GUI_MINIMAL_SCENE_SELECTOR = ".//plugin[@filename='MinimalScene']"
GUI_CAMERA_POSE_TAG = "camera_pose"
PROBE_PERFORMER_NAME = "probe_performer"

LEVEL_BUFFER_M = 30
LEVEL_Z_CENTER_M = 0
DEFAULT_LEVEL_Z_SIZE_M = 1500
PROBE_CLEARANCE_M = 30
CAMERA_CLEARANCE_M = 100
PROBE_MODEL = "level_probe"
COLLADA_NS = "http://www.collada.org/2005/11/COLLADASchema"
GUI_TEMPLATE = Path(__file__).parents[1] / TEMPLATES_DIR / GUI_TEMPLATE_FILE

ET.register_namespace(XML_DEFAULT_NAMESPACE_PREFIX, COLLADA_NS)


@dataclass(frozen=True)
class GazeboGenerationResult:
    model_count: int
    probe_pose: dict[str, float]
    gui_camera_pose: str
    level_z_size_m: float


def model_name(tile_stem: str) -> str:
    return f"{TERRAIN_MODEL_PREFIX}{tile_stem}"


def write_model_config(model_dir: Path, name: str) -> None:
    model_dir.joinpath(MODEL_CONFIG_FILE).write_text(
        f"""<?xml version="1.0"?>
<model>
  <name>{name}</name>
  <version>1.0</version>
  <sdf version="1.10">{MODEL_SDF_FILE}</sdf>
  <author>
    <name>dem2mesh</name>
  </author>
  <description>DEM mesh terrain tile generated from {name}.</description>
</model>
""",
        encoding=TEXT_ENCODING,
    )


def write_model_sdf(model_dir: Path, name: str, mesh_file: str) -> None:
    model_dir.joinpath(MODEL_SDF_FILE).write_text(
        f"""<?xml version="1.0"?>
<sdf version="1.10">
  <model name="{name}">
    <static>true</static>
    <link name="terrain_link">
      <visual name="terrain_visual">
        <geometry>
          <mesh>
            <uri>{MODEL_URI_PREFIX}{name}/{MESHES_DIR}/{mesh_file}</uri>
          </mesh>
        </geometry>
        <material>
          <diffuse>0.7 0.55 0.42 1</diffuse>
          <ambient>0.7 0.55 0.42 1</ambient>
          <pbr>
            <metal>
              <albedo_map>{MODEL_URI_PREFIX}{name}/{MATERIALS_DIR}/{TEXTURES_DIR}/{SOIL_TEXTURE_FILE}</albedo_map>
              <roughness>0.9</roughness>
              <metalness>0.0</metalness>
            </metal>
          </pbr>
        </material>
      </visual>
      <collision name="terrain_collision">
        <geometry>
          <mesh>
            <uri>{MODEL_URI_PREFIX}{name}/{MESHES_DIR}/{mesh_file}</uri>
          </mesh>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
""",
        encoding=TEXT_ENCODING,
    )


def write_probe_model(models_dir: Path) -> None:
    model_dir = models_dir / PROBE_MODEL
    model_dir.mkdir(parents=True, exist_ok=True)
    model_dir.joinpath(MODEL_CONFIG_FILE).write_text(
        f"""<?xml version="1.0"?>
<model>
  <name>{PROBE_MODEL}</name>
  <version>1.0</version>
  <sdf version="1.10">{MODEL_SDF_FILE}</sdf>
  <author>
    <name>dem2mesh</name>
  </author>
  <description>Floating performer marker for testing Gazebo level loading.</description>
</model>
""",
        encoding=TEXT_ENCODING,
    )
    model_dir.joinpath(MODEL_SDF_FILE).write_text(
        f"""<?xml version="1.0"?>
<sdf version="1.10">
  <model name="{PROBE_MODEL}">
    <static>false</static>
    <pose>0 0 0 0 0 0</pose>
    <link name="link">
      <kinematic>true</kinematic>
      <inertial>
        <mass>1.0</mass>
        <inertia>
          <ixx>0.1</ixx>
          <iyy>0.1</iyy>
          <izz>0.1</izz>
          <ixy>0</ixy>
          <ixz>0</ixz>
          <iyz>0</iyz>
        </inertia>
      </inertial>
      <visual name="visual">
        <geometry>
          <box>
            <size>12 12 12</size>
          </box>
        </geometry>
        <material>
          <ambient>1 0.15 0.05 1</ambient>
          <diffuse>1 0.15 0.05 1</diffuse>
          <emissive>0.4 0.02 0.0 1</emissive>
        </material>
      </visual>
      <collision name="collision">
        <geometry>
          <box>
            <size>12 12 12</size>
          </box>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
""",
        encoding=TEXT_ENCODING,
    )


def copy_dae_with_flat_normals_and_uv(src: Path, dst: Path) -> None:
    tree = ET.parse(src)
    root = tree.getroot()
    ns = {COLLADA_NAMESPACE_ALIAS: COLLADA_NS}

    mesh = root.find(COLLADA_MESH_SELECTOR, ns)
    if mesh is None:
        raise ValueError(f"missing Collada mesh: {src}")

    positions = mesh.find(COLLADA_POSITION_ARRAY_SELECTOR, ns)
    if positions is None:
        raise ValueError(f"missing Collada position array: {src}")
    vertex_count = int(positions.attrib[COLLADA_COUNT_ATTR]) // 3
    position_values = [float(value) for value in positions.text.split()]
    xy_values = [
        (position_values[i], position_values[i + 1])
        for i in range(0, len(position_values), 3)
    ]
    min_x = min(x for x, _ in xy_values)
    max_x = max(x for x, _ in xy_values)
    min_y = min(y for _, y in xy_values)
    max_y = max(y for _, y in xy_values)
    size_x = max(max_x - min_x, 1.0)
    size_y = max(max_y - min_y, 1.0)

    geometry = root.find(COLLADA_GEOMETRY_SELECTOR, ns)
    if geometry is None:
        raise ValueError(f"missing Collada geometry: {src}")
    geometry_id = geometry.attrib[COLLADA_ID_ATTR]
    normals_id = f"{geometry_id}{COLLADA_NORMAL_SUFFIX}"
    normals_array_id = f"{normals_id}{COLLADA_ARRAY_SUFFIX}"
    uv_id = f"{geometry_id}{COLLADA_UV_SUFFIX}"
    uv_array_id = f"{uv_id}{COLLADA_ARRAY_SUFFIX}"

    normal_source_selector = (
        f"{COLLADA_SOURCE_SELECTOR}[@{COLLADA_ID_ATTR}='{normals_id}']"
    )
    if mesh.find(normal_source_selector, ns) is None:
        source = ET.Element(
            f"{{{COLLADA_NS}}}{COLLADA_SOURCE_TAG}",
            {COLLADA_ID_ATTR: normals_id},
        )
        float_array = ET.SubElement(
            source,
            f"{{{COLLADA_NS}}}{COLLADA_FLOAT_ARRAY_TAG}",
            {
                COLLADA_ID_ATTR: normals_array_id,
                COLLADA_COUNT_ATTR: str(vertex_count * 3),
            },
        )
        float_array.text = " ".join([COLLADA_UP_NORMAL] * vertex_count)
        technique = ET.SubElement(
            source,
            f"{{{COLLADA_NS}}}{COLLADA_TECHNIQUE_COMMON_TAG}",
        )
        accessor = ET.SubElement(
            technique,
            f"{{{COLLADA_NS}}}{COLLADA_ACCESSOR_TAG}",
            {
                COLLADA_SOURCE_ATTR: f"#{normals_array_id}",
                COLLADA_COUNT_ATTR: str(vertex_count),
                COLLADA_STRIDE_ATTR: "3",
            },
        )
        ET.SubElement(
            accessor,
            f"{{{COLLADA_NS}}}{COLLADA_PARAM_TAG}",
            {COLLADA_NAME_ATTR: COLLADA_X_PARAM, COLLADA_TYPE_ATTR: COLLADA_FLOAT_TYPE},
        )
        ET.SubElement(
            accessor,
            f"{{{COLLADA_NS}}}{COLLADA_PARAM_TAG}",
            {COLLADA_NAME_ATTR: COLLADA_Y_PARAM, COLLADA_TYPE_ATTR: COLLADA_FLOAT_TYPE},
        )
        ET.SubElement(
            accessor,
            f"{{{COLLADA_NS}}}{COLLADA_PARAM_TAG}",
            {COLLADA_NAME_ATTR: COLLADA_Z_PARAM, COLLADA_TYPE_ATTR: COLLADA_FLOAT_TYPE},
        )
        mesh.insert(1, source)

    uv_source_selector = f"{COLLADA_SOURCE_SELECTOR}[@{COLLADA_ID_ATTR}='{uv_id}']"
    if mesh.find(uv_source_selector, ns) is None:
        source = ET.Element(
            f"{{{COLLADA_NS}}}{COLLADA_SOURCE_TAG}",
            {COLLADA_ID_ATTR: uv_id},
        )
        float_array = ET.SubElement(
            source,
            f"{{{COLLADA_NS}}}{COLLADA_FLOAT_ARRAY_TAG}",
            {
                COLLADA_ID_ATTR: uv_array_id,
                COLLADA_COUNT_ATTR: str(vertex_count * 2),
            },
        )
        float_array.text = " ".join(
            f"{(x - min_x) / size_x:.6f} {(y - min_y) / size_y:.6f}"
            for x, y in xy_values
        )
        technique = ET.SubElement(
            source,
            f"{{{COLLADA_NS}}}{COLLADA_TECHNIQUE_COMMON_TAG}",
        )
        accessor = ET.SubElement(
            technique,
            f"{{{COLLADA_NS}}}{COLLADA_ACCESSOR_TAG}",
            {
                COLLADA_SOURCE_ATTR: f"#{uv_array_id}",
                COLLADA_COUNT_ATTR: str(vertex_count),
                COLLADA_STRIDE_ATTR: "2",
            },
        )
        ET.SubElement(
            accessor,
            f"{{{COLLADA_NS}}}{COLLADA_PARAM_TAG}",
            {COLLADA_NAME_ATTR: COLLADA_S_PARAM, COLLADA_TYPE_ATTR: COLLADA_FLOAT_TYPE},
        )
        ET.SubElement(
            accessor,
            f"{{{COLLADA_NS}}}{COLLADA_PARAM_TAG}",
            {COLLADA_NAME_ATTR: COLLADA_T_PARAM, COLLADA_TYPE_ATTR: COLLADA_FLOAT_TYPE},
        )
        mesh.insert(2, source)

    triangles = mesh.find(COLLADA_TRIANGLES_SELECTOR, ns)
    if triangles is None:
        raise ValueError(f"missing Collada triangles: {src}")

    p = triangles.find(COLLADA_TRIANGLE_INDICES_SELECTOR, ns)
    if p is None or p.text is None:
        raise ValueError(f"missing Collada triangle indices: {src}")
    vertex_indices = p.text.split()

    if triangles.find(COLLADA_NORMAL_INPUT_SELECTOR, ns) is None:
        normal_input = ET.Element(
            f"{{{COLLADA_NS}}}{COLLADA_INPUT_TAG}",
            {
                COLLADA_SEMANTIC_ATTR: COLLADA_NORMAL_SEMANTIC,
                COLLADA_SOURCE_ATTR: f"#{normals_id}",
                COLLADA_OFFSET_ATTR: "1",
            },
        )
        triangles.insert(list(triangles).index(p), normal_input)

    if triangles.find(COLLADA_TEXCOORD_INPUT_SELECTOR, ns) is None:
        uv_input = ET.Element(
            f"{{{COLLADA_NS}}}{COLLADA_INPUT_TAG}",
            {
                COLLADA_SEMANTIC_ATTR: COLLADA_TEXCOORD_SEMANTIC,
                COLLADA_SOURCE_ATTR: f"#{uv_id}",
                COLLADA_OFFSET_ATTR: "2",
                COLLADA_SET_ATTR: "0",
            },
        )
        triangles.insert(list(triangles).index(p), uv_input)

    p.text = " ".join(f"{index} {index} {index}" for index in vertex_indices)
    tree.write(dst, encoding=TEXT_ENCODING, xml_declaration=True)


def read_tiles(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="") as f:
        return list(csv.DictReader(f))


def tile_size_m(tile: dict[str, str]) -> tuple[float, float]:
    width = float(tile[GAZEBO_CENTER_X_KEY]) - float(tile[GAZEBO_CORNER_X_KEY])
    height = float(tile[GAZEBO_CENTER_Y_KEY]) - float(tile[GAZEBO_CORNER_Y_KEY])
    return width * 2.0, height * 2.0


def dae_vertices(path: Path) -> list[tuple[float, float, float]]:
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {COLLADA_NAMESPACE_ALIAS: COLLADA_NS}
    positions = root.find(COLLADA_POSITION_ARRAY_ANYWHERE_SELECTOR, ns)
    if positions is None or positions.text is None:
        raise ValueError(f"missing Collada position array: {path}")

    values = [float(value) for value in positions.text.split()]
    if len(values) < 3:
        return []
    return [
        (values[index], values[index + 1], values[index + 2])
        for index in range(0, len(values), 3)
    ]


def dae_max_elevation(path: Path) -> float:
    vertices = dae_vertices(path)
    if not vertices:
        return 0.0
    return max(z for _x, _y, z in vertices)


def dae_center_elevation(path: Path) -> float:
    vertices = dae_vertices(path)
    if not vertices:
        return 0.0

    for x, y, z in vertices:
        if abs(x) < 1e-6 and abs(y) < 1e-6:
            return z

    _x, _y, z = min(
        vertices,
        key=lambda vertex: (vertex[0] * vertex[0]) + (vertex[1] * vertex[1]),
    )
    return z


def terrain_max_elevation(mesh_dir: Path, tiles: list[dict[str, str]]) -> float:
    max_elevation = 0.0
    for tile in tiles:
        mesh_path = mesh_dir / f"{Path(tile[TILE_FILE_KEY]).stem}{DAE_SUFFIX}"
        if not mesh_path.exists():
            continue
        max_elevation = max(max_elevation, dae_max_elevation(mesh_path))
    return max_elevation


def first_tile_center_elevation(mesh_dir: Path, tiles: list[dict[str, str]]) -> float:
    if not tiles:
        return 0.0

    mesh_path = mesh_dir / f"{Path(tiles[0][TILE_FILE_KEY]).stem}{DAE_SUFFIX}"
    if not mesh_path.exists():
        raise FileNotFoundError(f"missing mesh: {mesh_path}")
    return dae_center_elevation(mesh_path)


def terrain_footprint_m(tiles: list[dict[str, str]]) -> tuple[float, float]:
    if not tiles:
        return 0.0, 0.0

    west = min(float(tile[GAZEBO_CORNER_X_KEY]) for tile in tiles)
    south = min(float(tile[GAZEBO_CORNER_Y_KEY]) for tile in tiles)
    east = max(
        float(tile[GAZEBO_CENTER_X_KEY]) * 2.0 - float(tile[GAZEBO_CORNER_X_KEY])
        for tile in tiles
    )
    north = max(
        float(tile[GAZEBO_CENTER_Y_KEY]) * 2.0 - float(tile[GAZEBO_CORNER_Y_KEY])
        for tile in tiles
    )
    return east - west, north - south


def first_tile_center_xy(tiles: list[dict[str, str]]) -> tuple[float, float]:
    if not tiles:
        return 0.0, 0.0
    return float(tiles[0][GAZEBO_CENTER_X_KEY]), float(tiles[0][GAZEBO_CENTER_Y_KEY])


def camera_pose(tiles: list[dict[str, str]], first_tile_elevation_m: float = 0.0) -> str:
    x, y = first_tile_center_xy(tiles)
    z = first_tile_elevation_m + CAMERA_CLEARANCE_M
    return f"{x:.3f} {y:.3f} {z:.3f} 0 1.5708 0"


def probe_pose(tiles: list[dict[str, str]], first_tile_elevation_m: float = 0.0) -> tuple[float, float, float]:
    x, y = first_tile_center_xy(tiles)
    return x, y, first_tile_elevation_m + PROBE_CLEARANCE_M


def render_gui(camera_pose_value: str, template_path: Path = GUI_TEMPLATE) -> str:
    gui = ET.parse(template_path).getroot()
    minimal_scene = gui.find(GUI_MINIMAL_SCENE_SELECTOR)
    if minimal_scene is None:
        raise ValueError(f"missing MinimalScene plugin in GUI template: {template_path}")
    camera_pose_tag = minimal_scene.find(GUI_CAMERA_POSE_TAG)
    if camera_pose_tag is None:
        raise ValueError(f"missing camera_pose tag in GUI template: {template_path}")
    camera_pose_tag.text = camera_pose_value
    return ET.tostring(gui, encoding=XML_TEXT_ENCODING)


def create_models(tiles: list[dict[str, str]], mesh_dir: Path, texture: Path, models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)

    for tile in tiles:
        tile_stem = Path(tile[TILE_FILE_KEY]).stem
        name = model_name(tile_stem)
        mesh_src = mesh_dir / f"{tile_stem}{DAE_SUFFIX}"
        if not mesh_src.exists():
            raise FileNotFoundError(f"missing mesh: {mesh_src}")

        model_dir = models_dir / name
        model_mesh_dir = model_dir / MESHES_DIR
        texture_dir = model_dir / MATERIALS_DIR / TEXTURES_DIR
        model_mesh_dir.mkdir(parents=True, exist_ok=True)
        texture_dir.mkdir(parents=True, exist_ok=True)

        copy_dae_with_flat_normals_and_uv(mesh_src, model_mesh_dir / mesh_src.name)
        shutil.copy2(texture, texture_dir / SOIL_TEXTURE_FILE)
        write_model_config(model_dir, name)
        write_model_sdf(model_dir, name, mesh_src.name)

    write_probe_model(models_dir)


def world_sdf(
    tiles: list[dict[str, str]],
    world_name: str,
    first_tile_elevation_m: float = 0.0,
    level_z_size_m: float = DEFAULT_LEVEL_Z_SIZE_M,
) -> str:
    includes = []
    levels = []

    for tile in tiles:
        tile_stem = Path(tile[TILE_FILE_KEY]).stem
        name = model_name(tile_stem)
        x = float(tile[GAZEBO_CENTER_X_KEY])
        y = float(tile[GAZEBO_CENTER_Y_KEY])
        size_x, size_y = tile_size_m(tile)
        level_size_x = size_x
        level_size_y = size_y

        includes.append(
            f"""    <include>
      <name>{name}</name>
      <uri>{MODEL_URI_PREFIX}{name}</uri>
      <pose>{x:.3f} {y:.3f} 0 0 0 0</pose>
    </include>"""
        )

        levels.append(
            f"""      <level name="{LEVEL_PREFIX}{tile_stem}">
        <pose>{x:.3f} {y:.3f} {LEVEL_Z_CENTER_M:.3f} 0 0 0</pose>
        <geometry>
          <box>
            <size>{level_size_x:.3f} {level_size_y:.3f} {level_z_size_m:.3f}</size>
          </box>
        </geometry>
        <buffer>{LEVEL_BUFFER_M}</buffer>
        <ref>{name}</ref>
      </level>"""
        )

    includes_xml = "\n\n".join(includes)
    levels_xml = "\n\n".join(levels)
    first_x, first_y, first_z = probe_pose(tiles, first_tile_elevation_m)
    gui_xml = render_gui(camera_pose(tiles, first_tile_elevation_m))

    return f"""<?xml version="1.0"?>
<sdf version="1.10">
  <world name="{world_name}">
    <physics name="default_physics" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-rendering-system" name="gz::sim::systems::Rendering"/>

{gui_xml}

    <light name="sun" type="directional">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

{includes_xml}

    <include>
      <name>{PROBE_MODEL}</name>
      <uri>{MODEL_URI_PREFIX}{PROBE_MODEL}</uri>
      <pose>{first_x:.3f} {first_y:.3f} {first_z:.3f} 0 0 0</pose>
    </include>

    <plugin name="gz::sim" filename="dummy">
      <performer name="{PROBE_PERFORMER_NAME}">
        <ref>{PROBE_MODEL}</ref>
        <geometry>
          <box>
            <size>20 20 20</size>
          </box>
        </geometry>
      </performer>

{levels_xml}
    </plugin>
  </world>
</sdf>
"""


def single_world_sdf(
    tiles: list[dict[str, str]] | None = None,
    first_tile_elevation_m: float = 0.0,
) -> str:
    if tiles:
        first_x = float(tiles[0][GAZEBO_CENTER_X_KEY])
        first_y = float(tiles[0][GAZEBO_CENTER_Y_KEY])
        camera_tiles = tiles[:1]
    else:
        first_x = 0.0
        first_y = 0.0
        camera_tiles = []
    gui_xml = render_gui(camera_pose(camera_tiles, first_tile_elevation_m))

    return f"""<?xml version="1.0"?>
<sdf version="1.10">
  <world name="{SINGLE_TILE_WORLD_NAME}">
    <physics name="default_physics" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-rendering-system" name="gz::sim::systems::Rendering"/>

{gui_xml}

    <light name="sun" type="directional">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <include>
      <name>{SINGLE_TILE_MODEL_NAME}</name>
      <uri>{MODEL_URI_PREFIX}{SINGLE_TILE_MODEL_NAME}</uri>
      <pose>{first_x:.3f} {first_y:.3f} 0 0 0 0</pose>
    </include>
  </world>
</sdf>
"""


def travel_script(tiles: list[dict[str, str]], world_name: str, probe_z_m: float = 80.0) -> str:
    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        f'WORLD="${{1:-{world_name}}}"',
        f'Z="${{Z:-{probe_z_m:.3f}}}"',
        'SLEEP_S="${SLEEP_S:-1.0}"',
        'SERVICE="/world/${WORLD}/set_pose"',
        "",
        "move_probe() {",
        "  local x=\"$1\"",
        "  local y=\"$2\"",
        "  local z=\"$3\"",
        f"  echo \"moving {PROBE_MODEL} to x=${{x}} y=${{y}} z=${{z}}\"",
        "  gz service -s \"${SERVICE}\" \\",
        "    --reqtype gz.msgs.Pose \\",
        "    --reptype gz.msgs.Boolean \\",
        "    --timeout 2000 \\",
        f"    --req \"name: '{PROBE_MODEL}' position: "
        f"{{x: ${{x}} y: ${{y}} z: ${{z}}}} orientation: {{w: 1}}\" >/dev/null",
        "  sleep \"${SLEEP_S}\"",
        "}",
        "",
    ]

    sorted_tiles = sorted(
        tiles,
        key=lambda tile: (int(tile[TILE_Y_KEY]), int(tile[TILE_X_KEY])),
    )
    for tile in sorted_tiles:
        commands.append(
            "move_probe "
            f"{float(tile[GAZEBO_CENTER_X_KEY]):.3f} "
            f"{float(tile[GAZEBO_CENTER_Y_KEY]):.3f} "
            '"${Z}"'
        )

    commands.append("")
    return "\n".join(commands)


def readme_text() -> str:
    return f"""# Generated Gazebo level terrain

```bash
export GZ_SIM_RESOURCE_PATH=$PWD/{MODELS_DIR}
gz sim --levels {LEVELS_TERRAIN_SDF}
```

In another terminal, move the floating performer marker through each level:

```bash
./{TRAVEL_LEVELS_SCRIPT}
```

The world contains `{PROBE_MODEL}` as a floating kinematic box and registers it as
the level performer. Each generated level references only its own terrain tile.

Without `--levels`, Gazebo loads every model at startup, so level load/unload
behavior is not exercised.
"""


def generate_gazebo_worlds(
    manifest_path: Path,
    mesh_dir: Path,
    texture: Path,
    gz_dir: Path,
    world_name: str,
    level_z_size_m: float = DEFAULT_LEVEL_Z_SIZE_M,
) -> GazeboGenerationResult:
    """
    - create mesh models
    - write level-aware world SDF
    - write single-level world SDF for testing
    - write travel script for moving probe through levels
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing tile manifest: {manifest_path}")
    if not texture.exists():
        raise FileNotFoundError(f"missing texture: {texture}")

    tiles = read_tiles(manifest_path)
    if not tiles:
        raise RuntimeError(f"tile manifest is empty: {manifest_path}")

    first_tile_elevation_m = first_tile_center_elevation(mesh_dir, tiles)
    probe_x, probe_y, probe_z = probe_pose(tiles, first_tile_elevation_m)
    camera_pose_value = camera_pose(tiles, first_tile_elevation_m)

    models_dir = gz_dir / MODELS_DIR
    create_models(tiles, mesh_dir, texture, models_dir)
    gz_dir.mkdir(parents=True, exist_ok=True)

    (gz_dir / LEVELS_TERRAIN_SDF).write_text(
        world_sdf(tiles, world_name, first_tile_elevation_m, level_z_size_m),
        encoding=TEXT_ENCODING,
    )
    (gz_dir / SINGLE_TILE_TERRAIN_SDF).write_text(
        single_world_sdf(tiles, first_tile_elevation_m),
        encoding=TEXT_ENCODING,
    )
    travel_path = gz_dir / TRAVEL_LEVELS_SCRIPT
    travel_path.write_text(
        travel_script(tiles, world_name, probe_z),
        encoding=TEXT_ENCODING,
    )
    travel_path.chmod(0o755)
    (gz_dir / README_FILE).write_text(readme_text(), encoding=TEXT_ENCODING)
    return GazeboGenerationResult(
        model_count=len(tiles),
        probe_pose={
            RESULT_X_KEY: probe_x,
            RESULT_Y_KEY: probe_y,
            RESULT_Z_KEY: probe_z,
        },
        gui_camera_pose=camera_pose_value,
        level_z_size_m=level_z_size_m,
    )
