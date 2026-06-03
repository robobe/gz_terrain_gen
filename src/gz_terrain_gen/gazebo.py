import csv
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET

LEVEL_BUFFER_M = 30
LEVEL_Z_CENTER_M = 0
LEVEL_Z_SIZE_M = 200
PROBE_MODEL = "level_probe"
COLLADA_NS = "http://www.collada.org/2005/11/COLLADASchema"

ET.register_namespace("", COLLADA_NS)


def model_name(tile_stem: str) -> str:
    return f"terrain_{tile_stem}"


def write_model_config(model_dir: Path, name: str) -> None:
    model_dir.joinpath("model.config").write_text(
        f"""<?xml version="1.0"?>
<model>
  <name>{name}</name>
  <version>1.0</version>
  <sdf version="1.10">model.sdf</sdf>
  <author>
    <name>dem2mesh</name>
  </author>
  <description>DEM mesh terrain tile generated from {name}.</description>
</model>
"""
    )


def write_model_sdf(model_dir: Path, name: str, mesh_file: str) -> None:
    model_dir.joinpath("model.sdf").write_text(
        f"""<?xml version="1.0"?>
<sdf version="1.10">
  <model name="{name}">
    <static>true</static>
    <link name="terrain_link">
      <visual name="terrain_visual">
        <geometry>
          <mesh>
            <uri>model://{name}/meshes/{mesh_file}</uri>
          </mesh>
        </geometry>
        <material>
          <diffuse>0.7 0.55 0.42 1</diffuse>
          <ambient>0.7 0.55 0.42 1</ambient>
          <pbr>
            <metal>
              <albedo_map>model://{name}/materials/textures/soil.jpg</albedo_map>
              <roughness>0.9</roughness>
              <metalness>0.0</metalness>
            </metal>
          </pbr>
        </material>
      </visual>
      <collision name="terrain_collision">
        <geometry>
          <mesh>
            <uri>model://{name}/meshes/{mesh_file}</uri>
          </mesh>
        </geometry>
      </collision>
    </link>
  </model>
</sdf>
"""
    )


def write_probe_model(models_dir: Path) -> None:
    model_dir = models_dir / PROBE_MODEL
    model_dir.mkdir(parents=True, exist_ok=True)
    model_dir.joinpath("model.config").write_text(
        f"""<?xml version="1.0"?>
<model>
  <name>{PROBE_MODEL}</name>
  <version>1.0</version>
  <sdf version="1.10">model.sdf</sdf>
  <author>
    <name>dem2mesh</name>
  </author>
  <description>Floating performer marker for testing Gazebo level loading.</description>
</model>
"""
    )
    model_dir.joinpath("model.sdf").write_text(
        f"""<?xml version="1.0"?>
<sdf version="1.10">
  <model name="{PROBE_MODEL}">
    <static>false</static>
    <pose>0 0 80 0 0 0</pose>
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
"""
    )


def copy_dae_with_flat_normals_and_uv(src: Path, dst: Path) -> None:
    tree = ET.parse(src)
    root = tree.getroot()
    ns = {"c": COLLADA_NS}

    mesh = root.find(".//c:mesh", ns)
    if mesh is None:
        raise ValueError(f"missing Collada mesh: {src}")

    positions = mesh.find("c:source/c:float_array", ns)
    if positions is None:
        raise ValueError(f"missing Collada position array: {src}")
    vertex_count = int(positions.attrib["count"]) // 3
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

    geometry = root.find(".//c:geometry", ns)
    if geometry is None:
        raise ValueError(f"missing Collada geometry: {src}")
    geometry_id = geometry.attrib["id"]
    normals_id = f"{geometry_id}-normals"
    normals_array_id = f"{normals_id}-array"
    uv_id = f"{geometry_id}-uv"
    uv_array_id = f"{uv_id}-array"

    if mesh.find(f"c:source[@id='{normals_id}']", ns) is None:
        source = ET.Element(f"{{{COLLADA_NS}}}source", {"id": normals_id})
        float_array = ET.SubElement(
            source,
            f"{{{COLLADA_NS}}}float_array",
            {"id": normals_array_id, "count": str(vertex_count * 3)},
        )
        float_array.text = " ".join(["0 0 1"] * vertex_count)
        technique = ET.SubElement(source, f"{{{COLLADA_NS}}}technique_common")
        accessor = ET.SubElement(
            technique,
            f"{{{COLLADA_NS}}}accessor",
            {"source": f"#{normals_array_id}", "count": str(vertex_count), "stride": "3"},
        )
        ET.SubElement(accessor, f"{{{COLLADA_NS}}}param", {"name": "X", "type": "float"})
        ET.SubElement(accessor, f"{{{COLLADA_NS}}}param", {"name": "Y", "type": "float"})
        ET.SubElement(accessor, f"{{{COLLADA_NS}}}param", {"name": "Z", "type": "float"})
        mesh.insert(1, source)

    if mesh.find(f"c:source[@id='{uv_id}']", ns) is None:
        source = ET.Element(f"{{{COLLADA_NS}}}source", {"id": uv_id})
        float_array = ET.SubElement(
            source,
            f"{{{COLLADA_NS}}}float_array",
            {"id": uv_array_id, "count": str(vertex_count * 2)},
        )
        float_array.text = " ".join(
            f"{(x - min_x) / size_x:.6f} {(y - min_y) / size_y:.6f}"
            for x, y in xy_values
        )
        technique = ET.SubElement(source, f"{{{COLLADA_NS}}}technique_common")
        accessor = ET.SubElement(
            technique,
            f"{{{COLLADA_NS}}}accessor",
            {"source": f"#{uv_array_id}", "count": str(vertex_count), "stride": "2"},
        )
        ET.SubElement(accessor, f"{{{COLLADA_NS}}}param", {"name": "S", "type": "float"})
        ET.SubElement(accessor, f"{{{COLLADA_NS}}}param", {"name": "T", "type": "float"})
        mesh.insert(2, source)

    triangles = mesh.find("c:triangles", ns)
    if triangles is None:
        raise ValueError(f"missing Collada triangles: {src}")

    p = triangles.find("c:p", ns)
    if p is None or p.text is None:
        raise ValueError(f"missing Collada triangle indices: {src}")
    vertex_indices = p.text.split()

    if triangles.find("c:input[@semantic='NORMAL']", ns) is None:
        normal_input = ET.Element(
            f"{{{COLLADA_NS}}}input",
            {"semantic": "NORMAL", "source": f"#{normals_id}", "offset": "1"},
        )
        triangles.insert(list(triangles).index(p), normal_input)

    if triangles.find("c:input[@semantic='TEXCOORD']", ns) is None:
        uv_input = ET.Element(
            f"{{{COLLADA_NS}}}input",
            {"semantic": "TEXCOORD", "source": f"#{uv_id}", "offset": "2", "set": "0"},
        )
        triangles.insert(list(triangles).index(p), uv_input)

    p.text = " ".join(f"{index} {index} {index}" for index in vertex_indices)
    tree.write(dst, encoding="utf-8", xml_declaration=True)


def read_tiles(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="") as f:
        return list(csv.DictReader(f))


def tile_size_m(tile: dict[str, str]) -> tuple[float, float]:
    width = float(tile["gazebo_center_x_m"]) - float(tile["gazebo_corner_x_m"])
    height = float(tile["gazebo_center_y_m"]) - float(tile["gazebo_corner_y_m"])
    return width * 2.0, height * 2.0


def create_models(tiles: list[dict[str, str]], mesh_dir: Path, texture: Path, models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)

    for tile in tiles:
        tile_stem = Path(tile["file"]).stem
        name = model_name(tile_stem)
        mesh_src = mesh_dir / f"{tile_stem}.dae"
        if not mesh_src.exists():
            raise FileNotFoundError(f"missing mesh: {mesh_src}")

        model_dir = models_dir / name
        model_mesh_dir = model_dir / "meshes"
        texture_dir = model_dir / "materials" / "textures"
        model_mesh_dir.mkdir(parents=True, exist_ok=True)
        texture_dir.mkdir(parents=True, exist_ok=True)

        copy_dae_with_flat_normals_and_uv(mesh_src, model_mesh_dir / mesh_src.name)
        shutil.copy2(texture, texture_dir / "soil.jpg")
        write_model_config(model_dir, name)
        write_model_sdf(model_dir, name, mesh_src.name)

    write_probe_model(models_dir)


def world_sdf(tiles: list[dict[str, str]]) -> str:
    includes = []
    levels = []

    for tile in tiles:
        tile_stem = Path(tile["file"]).stem
        name = model_name(tile_stem)
        x = float(tile["gazebo_center_x_m"])
        y = float(tile["gazebo_center_y_m"])
        size_x, size_y = tile_size_m(tile)
        level_size_x = size_x + (2 * LEVEL_BUFFER_M)
        level_size_y = size_y + (2 * LEVEL_BUFFER_M)

        includes.append(
            f"""    <include>
      <name>{name}</name>
      <uri>model://{name}</uri>
      <pose>{x:.3f} {y:.3f} 0 0 0 0</pose>
    </include>"""
        )

        levels.append(
            f"""      <level name="level_{tile_stem}">
        <pose>{x:.3f} {y:.3f} {LEVEL_Z_CENTER_M:.3f} 0 0 0</pose>
        <geometry>
          <box>
            <size>{level_size_x:.3f} {level_size_y:.3f} {LEVEL_Z_SIZE_M:.3f}</size>
          </box>
        </geometry>
        <buffer>{LEVEL_BUFFER_M}</buffer>
        <ref>{name}</ref>
      </level>"""
        )

    includes_xml = "\n\n".join(includes)
    levels_xml = "\n\n".join(levels)
    first_x = float(tiles[0]["gazebo_center_x_m"])
    first_y = float(tiles[0]["gazebo_center_y_m"])

    return f"""<?xml version="1.0"?>
<sdf version="1.10">
  <world name="dem_mesh_levels">
    <physics name="default_physics" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>

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
      <uri>model://{PROBE_MODEL}</uri>
      <pose>{first_x:.3f} {first_y:.3f} 80 0 0 0</pose>
    </include>

    <plugin name="gz::sim" filename="dummy">
      <performer name="probe_performer">
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


def single_world_sdf() -> str:
    return """<?xml version="1.0"?>
<sdf version="1.10">
  <world name="single_tile_terrain">
    <physics name="default_physics" type="ignored">
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1.0</real_time_factor>
    </physics>

    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"/>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>

    <light name="sun" type="directional">
      <cast_shadows>true</cast_shadows>
      <pose>0 0 100 0 0 0</pose>
      <diffuse>0.8 0.8 0.8 1</diffuse>
      <specular>0.2 0.2 0.2 1</specular>
      <direction>-0.5 0.1 -0.9</direction>
    </light>

    <include>
      <name>terrain_tile_0_0</name>
      <uri>model://terrain_tile_0_0</uri>
      <pose>0 0 0 0 0 0</pose>
    </include>
  </world>
</sdf>
"""


def travel_script(tiles: list[dict[str, str]]) -> str:
    commands = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        'WORLD="${1:-dem_mesh_levels}"',
        'Z="${Z:-80}"',
        'SLEEP_S="${SLEEP_S:-1.0}"',
        'SERVICE="/world/${WORLD}/set_pose"',
        "",
        "move_probe() {",
        "  local x=\"$1\"",
        "  local y=\"$2\"",
        "  local z=\"$3\"",
        "  echo \"moving level_probe to x=${x} y=${y} z=${z}\"",
        "  gz service -s \"${SERVICE}\" \\",
        "    --reqtype gz.msgs.Pose \\",
        "    --reptype gz.msgs.Boolean \\",
        "    --timeout 2000 \\",
        "    --req \"name: 'level_probe' position: {x: ${x} y: ${y} z: ${z}} orientation: {w: 1}\" >/dev/null",
        "  sleep \"${SLEEP_S}\"",
        "}",
        "",
    ]

    sorted_tiles = sorted(
        tiles,
        key=lambda tile: (int(tile["tile_y"]), int(tile["tile_x"])),
    )
    for tile in sorted_tiles:
        commands.append(
            "move_probe "
            f"{float(tile['gazebo_center_x_m']):.3f} "
            f"{float(tile['gazebo_center_y_m']):.3f} "
            '"${Z}"'
        )

    commands.append("")
    return "\n".join(commands)


def readme_text() -> str:
    return """# Generated Gazebo level terrain

```bash
export GZ_SIM_RESOURCE_PATH=$PWD/models
gz sim --levels levels_terrain.sdf
```

In another terminal, move the floating performer marker through each level:

```bash
./travel_levels.sh
```

The world contains `level_probe` as a floating kinematic box and registers it as
the level performer. Each generated level references only its own terrain tile.

Without `--levels`, Gazebo loads every model at startup, so level load/unload
behavior is not exercised.
"""


def generate_gazebo_worlds(manifest_path: Path, mesh_dir: Path, texture: Path, gz_dir: Path) -> int:
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing tile manifest: {manifest_path}")
    if not texture.exists():
        raise FileNotFoundError(f"missing texture: {texture}")

    tiles = read_tiles(manifest_path)
    if not tiles:
        raise RuntimeError(f"tile manifest is empty: {manifest_path}")

    models_dir = gz_dir / "models"
    create_models(tiles, mesh_dir, texture, models_dir)
    gz_dir.mkdir(parents=True, exist_ok=True)

    (gz_dir / "levels_terrain.sdf").write_text(world_sdf(tiles))
    (gz_dir / "single_tile_terrain.sdf").write_text(single_world_sdf())
    travel_path = gz_dir / "travel_levels.sh"
    travel_path.write_text(travel_script(tiles))
    travel_path.chmod(0o755)
    (gz_dir / "README.md").write_text(readme_text())
    return len(tiles)
