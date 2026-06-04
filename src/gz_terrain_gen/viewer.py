import csv
from dataclasses import dataclass
import functools
import http.server
import socketserver
import webbrowser
from pathlib import Path

import click
import numpy as np
import trimesh
from loguru import logger

from gz_terrain_gen.mesh import open_dem, tile_to_mesh
from gz_terrain_gen.paths import DEFAULT_OUTPUT_DIR, validate_world_name

VIEWER_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>GZ Terrain Viewer</title>
  <style>
    html, body {
      margin: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      background: #151515;
      color: #f2f2f2;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    #status {
      position: fixed;
      left: 16px;
      bottom: 16px;
      padding: 8px 10px;
      background: rgba(0, 0, 0, 0.58);
      border-radius: 6px;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <div id="status">Loading terrain.glb</div>
  <script type="importmap">
    {
      "imports": {
        "three": "https://unpkg.com/three@0.179.1/build/three.module.js",
        "three/addons/": "https://unpkg.com/three@0.179.1/examples/jsm/"
      }
    }
  </script>
  <script type="module">
    import * as THREE from "three";
    import { OrbitControls } from "three/addons/controls/OrbitControls.js";
    import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x151515);

    const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 100000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    document.body.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    scene.add(new THREE.HemisphereLight(0xffffff, 0x2c2c2c, 2.1));
    const sun = new THREE.DirectionalLight(0xffffff, 1.2);
    sun.position.set(200, -300, 500);
    scene.add(sun);

    const grid = new THREE.GridHelper(1200, 12, 0x555555, 0x333333);
    grid.rotation.x = Math.PI / 2;
    scene.add(grid);

    const status = document.getElementById("status");
    const loader = new GLTFLoader();
    loader.load("terrain.glb", (gltf) => {
      const terrain = gltf.scene;
      scene.add(terrain);

      const box = new THREE.Box3().setFromObject(terrain);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      const radius = Math.max(size.x, size.y, size.z, 1);

      controls.target.copy(center);
      camera.position.set(center.x + radius * 0.75, center.y - radius * 1.1, center.z + radius * 0.65);
      camera.near = Math.max(radius / 1000, 0.1);
      camera.far = radius * 10;
      camera.updateProjectionMatrix();
      controls.update();

      status.textContent = `Loaded terrain.glb | ${Math.round(size.x)}m x ${Math.round(size.y)}m`;
    }, undefined, (error) => {
      console.error(error);
      status.textContent = "Failed to load terrain.glb";
    });

    window.addEventListener("resize", () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });

    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    animate();
  </script>
</body>
</html>
"""


@dataclass(frozen=True)
class ViewerGenerationResult:
    viewer_dir: Path
    glb_path: Path
    html_path: Path
    vertex_count: int
    face_count: int


def click_world_name(_ctx: click.Context, _param: click.Parameter, value: str) -> str:
    try:
        return validate_world_name(value)
    except ValueError as exc:
        raise click.BadParameter(str(exc)) from exc


def read_manifest(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="") as manifest:
        return list(csv.DictReader(manifest))


def terrain_vertex_colors(vertices: np.ndarray) -> np.ndarray:
    z = vertices[:, 2]
    z_min = float(np.min(z))
    z_max = float(np.max(z))
    if z_max == z_min:
        normalized = np.zeros_like(z)
    else:
        normalized = (z - z_min) / (z_max - z_min)

    low = np.array([69, 132, 79], dtype=np.float64)
    mid = np.array([166, 139, 91], dtype=np.float64)
    high = np.array([238, 238, 232], dtype=np.float64)
    colors = np.empty((len(vertices), 4), dtype=np.uint8)

    lower = normalized <= 0.55
    lower_scale = np.divide(normalized, 0.55, out=np.zeros_like(normalized), where=lower)
    upper_scale = np.divide(normalized - 0.55, 0.45, out=np.zeros_like(normalized), where=~lower)
    colors[lower, :3] = (low + (mid - low) * lower_scale[lower, None]).astype(np.uint8)
    colors[~lower, :3] = (mid + (high - mid) * upper_scale[~lower, None]).astype(np.uint8)
    colors[:, 3] = 255
    return colors


def build_combined_terrain_mesh(source_dem: Path, tiles_dir: Path, manifest_path: Path) -> trimesh.Trimesh:
    if not source_dem.exists():
        raise FileNotFoundError(f"missing DEM: {source_dem}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"missing tile manifest: {manifest_path}")

    tiles = read_manifest(manifest_path)
    if not tiles:
        raise RuntimeError(f"tile manifest is empty: {manifest_path}")

    source = open_dem(source_dem)
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []

    for tile in tiles:
        tile_vertices, tile_faces = tile_to_mesh(tile, source, tiles_dir)
        x_offset = float(tile["gazebo_center_x_m"])
        y_offset = float(tile["gazebo_center_y_m"])
        vertex_offset = len(vertices)

        vertices.extend((x + x_offset, y + y_offset, z) for x, y, z in tile_vertices)
        faces.extend((a + vertex_offset, b + vertex_offset, c + vertex_offset) for a, b, c in tile_faces)

    vertex_array = np.array(vertices, dtype=np.float64)
    face_array = np.array(faces, dtype=np.int64)
    terrain = trimesh.Trimesh(vertices=vertex_array, faces=face_array, process=False)
    terrain.visual.vertex_colors = terrain_vertex_colors(vertex_array)
    return terrain


def write_viewer_html(path: Path) -> None:
    path.write_text(VIEWER_HTML)


def generate_viewer(source_dem: Path, tiles_dir: Path, manifest_path: Path, viewer_dir: Path) -> ViewerGenerationResult:
    logger.info("starting browser viewer generation")
    logger.debug("viewer output directory: {}", viewer_dir)
    viewer_dir.mkdir(parents=True, exist_ok=True)

    terrain = build_combined_terrain_mesh(source_dem, tiles_dir, manifest_path)
    glb_path = viewer_dir / "terrain.glb"
    html_path = viewer_dir / "index.html"
    terrain.export(glb_path, file_type="glb")
    write_viewer_html(html_path)

    logger.info("completed browser viewer generation: {}", glb_path)
    return ViewerGenerationResult(
        viewer_dir=viewer_dir,
        glb_path=glb_path,
        html_path=html_path,
        vertex_count=int(len(terrain.vertices)),
        face_count=int(len(terrain.faces)),
    )


def serve_viewer(viewer_dir: Path, host: str, port: int, open_browser: bool) -> None:
    if not viewer_dir.exists():
        raise FileNotFoundError(f"missing viewer directory: {viewer_dir}")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(viewer_dir))
    with socketserver.TCPServer((host, port), handler) as server:
        url = f"http://{host}:{port}/"
        click.echo(f"serving viewer at {url}")
        click.echo(f"viewer directory: {viewer_dir}")
        if open_browser:
            webbrowser.open(url)
        server.serve_forever()


@click.command(help="Serve a generated terrain browser viewer.")
@click.option("--world-name", default="terrain_world", show_default=True, callback=click_world_name)
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    default=DEFAULT_OUTPUT_DIR,
    show_default=True,
)
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", type=int, default=8000, show_default=True)
@click.option("--open", "open_browser", is_flag=True, help="Open the viewer URL in a browser.")
def viewer_cli(world_name: str, output_dir: Path, host: str, port: int, open_browser: bool) -> None:
    viewer_dir = output_dir / world_name / "viewer"
    serve_viewer(viewer_dir, host, port, open_browser)
