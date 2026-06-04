# GZ Terrain Generator

This project generates tiled Gazebo terrain from real elevation data. It downloads
a DEM from OpenTopography, splits it into tiles, converts tiles into Collada
meshes, and creates Gazebo model/world files for testing level loading with
`gz sim --levels`. It also creates a browser viewer for inspecting the combined
terrain mesh without Gazebo.

The Python project is managed with `uv` and exposes one CLI command:

```bash
gz-terrain-gen
```

## Setup

Create or update the local virtual environment:

```bash
uv sync
```

`uv` creates `.venv/` at the repository root. You do not need to activate it for
normal use; prefer `uv run`:

```bash
uv run gz-terrain-gen --help
uv run pytest
```

Activation is optional:

```bash
source .venv/bin/activate
gz-terrain-gen --help
```

To recreate the environment:

```bash
rm -rf .venv
uv sync
```

## Generate Terrain

Run the full pipeline from the repository root:

```bash
export OPENTOPOGRAPHY_API_KEY=your_api_key
uv run gz-terrain-gen
uv run gz-terrain-gen --world-name demo_world
```

Use an existing GeoTIFF DEM instead of downloading from OpenTopography:

```bash
uv run gz-terrain-gen --world-name demo_world --dem-file /path/to/dem.tif
```

When `--dem-file` is provided, `OPENTOPOGRAPHY_API_KEY` is not required. The DEM
is copied into `outputs/<world-name>/dem.tif` and used by all later stages.

Generated artifacts are written under `outputs/<world-name>/` by default. If the
target world folder already exists, the CLI asks before removing it and
continuing. Mesh Z values are normalized so the minimum terrain elevation aligns
with Gazebo Z `0`; the subtracted elevation offset is recorded in
`metadata.json`.

```text
outputs/demo_world/
├── metadata.json
├── dem.tif
├── tiles/
├── mesh/
├── gz/
└── viewer/
```

Inspect the combined terrain mesh without Gazebo:

```bash
uv run gz-terrain-gen-viewer --world-name demo_world
```

Then open the printed local URL in a browser. The viewer loads
`outputs/demo_world/viewer/terrain.glb` from `viewer/index.html`. It uses
Three.js from a CDN, so the browser needs internet access unless the viewer is
changed later to vendor Three.js locally.

Run the generated Gazebo world:

```bash
cd outputs/demo_world/gz
export GZ_SIM_RESOURCE_PATH=$PWD/models
gz sim --levels levels_terrain.sdf
```

In a second terminal:

```bash
cd outputs/demo_world/gz
./travel_levels.sh
```

## CLI Commands

```bash
uv run gz-terrain-gen
uv run gz-terrain-gen --world-name demo_world
uv run gz-terrain-gen --world-name demo_world --center-lat 30.853205 --center-lon 34.447382 --size-km 1.0
uv run gz-terrain-gen --world-name demo_world --dem-file /path/to/dem.tif
uv run gz-terrain-gen --world-name demo_world --level-z-size-m 1500
uv run gz-terrain-gen-viewer --world-name demo_world
```

`--world-name` is optional and defaults to `terrain_world`. Use `--output-dir`
to choose a different generated artifact root. Gazebo level geometry Z size
defaults to `1500` meters and can be changed with `--level-z-size-m`; level X/Y
size is generated from each tile size.

```bash
uv run gz-terrain-gen --help
```

## Project Layout

```text
src/gz_terrain_gen/
├── main.py
├── cli.py
├── opentopo.py
├── tiling.py
├── mesh.py
├── metadata.py
├── viewer.py
└── gazebo.py
```

New source changes should go under `src/gz_terrain_gen/`; new generated terrain
output should go under `outputs/`.

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Gazebo usage](docs/gazebo.md)
- [Agent instructions](AGENTS.md)
- [Plan records](plans/README.md)

## Dependencies

Python dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
Raster reads use `rasterio`; combined viewer export uses `trimesh` and
`pygltflib`.

```bash
uv run python -c "import rasterio, trimesh, pygltflib; print('deps ok')"
```

Gazebo itself remains a system dependency for simulation.
