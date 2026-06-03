# Architecture

This project is now a packaged Python application managed by `uv`. The CLI
command `gz-terrain-gen` runs a staged terrain-generation pipeline. Each stage
reads files written by the previous stage and writes the next set of terrain
artifacts under `outputs/` by default.

## Data Flow

```text
OpenTopography API
  -> outputs/dem_1km.tif
  -> outputs/tiles/tile_X_Y.tif
  -> outputs/tiles/tiles.csv
  -> outputs/mesh/tile_X_Y.dae
  -> outputs/gz/models/terrain_tile_X_Y/
  -> outputs/gz/levels_terrain.sdf
  -> outputs/gz/travel_levels.sh
```

## Components

### DEM Download

Module: `src/gz_terrain_gen/opentopo.py`

Responsibilities:

- Reads `OPENTOPOGRAPHY_API_KEY`.
- Defines a hard-coded center point and square area.
- Calls the OpenTopography `globaldem` endpoint for COP30 data.
- Writes `outputs/dem_1km.tif` by default.

### DEM Tiling

Module: `src/gz_terrain_gen/tiling.py`

Responsibilities:

- Reads `outputs/dem_1km.tif` by default.
- Converts a 200 m tile size into latitude/longitude degree increments.
- Writes each tile to `outputs/tiles/tile_X_Y.tif`.
- Writes `outputs/tiles/tiles.csv` with tile bounds and Gazebo placement metadata.

Important contract:

- `tiles.csv` is the manifest used by all later stages.

### Mesh Generation

Module: `src/gz_terrain_gen/mesh.py`

Responsibilities:

- Reads `outputs/tiles/tiles.csv`.
- Opens `outputs/dem_1km.tif` with GDAL.
- Samples the DEM using bilinear interpolation.
- Builds a local mesh for each tile where X/Y are tile-local meters and Z is
  DEM elevation.
- Writes `outputs/mesh/tile_X_Y.dae`.

Important contract:

- Meshes are centered around local `(0, 0)` and later placed in Gazebo using the
  center coordinates from `tiles.csv`.

### Gazebo Generation

Module: `src/gz_terrain_gen/gazebo.py`

Responsibilities:

- Reads `outputs/mesh/*.dae`, `outputs/tiles/tiles.csv`, and
  `assets/texture/soil.jpg` by default.
- Adds flat normals and UVs to each Collada mesh.
- Creates one Gazebo model per terrain tile.
- Creates `outputs/gz/levels_terrain.sdf` with a level for each terrain tile.
- Creates `outputs/gz/single_tile_terrain.sdf` for simpler inspection.
- Creates a `level_probe` performer model and `outputs/gz/travel_levels.sh`.

Important contract:

- `gz sim --levels levels_terrain.sdf` uses the performer location to exercise
  Gazebo level loading.

## Current Repository Shape

```text
.
├── README.md
├── AGENTS.md
├── docs/
├── pyproject.toml
├── uv.lock
├── assets/
│   └── texture/
├── plans/
├── src/
│   └── gz_terrain_gen/
├── tests/
└── outputs/
```

## Package Architecture

```text
src/gz_terrain_gen/
  cli.py
  opentopo.py
  tiling.py
  mesh.py
  gazebo.py
  paths.py
```

- A CLI command controls the whole pipeline.
- All paths are explicit and configurable.
- Generated artifacts go under `outputs/` or another configured directory.
- Unit tests cover manifest generation, interpolation, mesh topology, and SDF
  generation without needing Gazebo.

## Key Design Decisions To Make

- Configuration format: command-line flags only, YAML/TOML config, or both.
- Output policy: keep generated DEM/mesh/Gazebo files out of git by default.
- Coordinate model: document whether Gazebo X/Y origin is the southwest corner,
  DEM center, or configurable origin.
- Height handling: decide whether raw DEM elevations should be preserved,
  normalized, offset to zero, or scaled.
- Mesh density: decide whether to use every DEM pixel or resample to a target
  mesh resolution for performance.
