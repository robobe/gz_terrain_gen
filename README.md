# GZ Terrain Generator

This project generates tiled Gazebo terrain from real elevation data. It downloads
a DEM from OpenTopography, splits it into tiles, converts tiles into Collada
meshes, and creates Gazebo model/world files for testing level loading with
`gz sim --levels`.

The Python project is managed with `uv` and exposes one CLI command:

```bash
gz-terrain-gen
```

## Setup

Install the system tools used by the pipeline. The Python GDAL binding is locked
in `pyproject.toml`, but it needs matching system GDAL libraries and headers:

```bash
sudo apt install gdal-bin libgdal-dev python3-gdal
```

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

Generated artifacts are written under `outputs/<world-name>/` by default. If the
target world folder already exists, the CLI asks before removing it and
continuing.

```text
outputs/demo_world/
├── metadata.json
├── dem.tif
├── tiles/
├── mesh/
└── gz/
```

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
```

`--world-name` is optional and defaults to `terrain_world`. Use `--output-dir`
to choose a different generated artifact root.

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
The mesh stage imports `osgeo.gdal`; the project pins `GDAL==3.8.4` to match the
system GDAL version on this machine.

Verify the binding with:

```bash
uv run python -c "from osgeo import gdal"
```

If it fails on another machine, install matching system GDAL packages and rerun
`uv sync`, or update the pinned `GDAL` version to match `gdal-config --version`.
