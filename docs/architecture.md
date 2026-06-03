# Architecture

This project creates terrain layouts for Gazebo from real elevation data. It
downloads a DEM from a source such as OpenTopography, splits the DEM into
smaller terrain tiles for Gazebo performance, converts each tile into a Collada
`.dae` mesh, and wraps each mesh in a Gazebo model with visual, collision, and
texture data.

The application also creates Gazebo worlds with level definitions. Those levels
can load and unload terrain models based on the performer position. Generated
artifacts are grouped by CLI world name under `outputs/<world-name>/`. A browser
viewer is also generated for inspecting the combined terrain mesh without
Gazebo.

## Data Flow

```text
OpenTopography API
  -> outputs/<world-name>/metadata.json
  -> outputs/<world-name>/dem.tif
  -> outputs/<world-name>/tiles/tile_X_Y.tif
  -> outputs/<world-name>/tiles/tiles.csv
  -> outputs/<world-name>/mesh/tile_X_Y.dae
  -> outputs/<world-name>/gz/models/terrain_tile_X_Y/
  -> outputs/<world-name>/gz/levels_terrain.sdf
  -> outputs/<world-name>/gz/travel_levels.sh
  -> outputs/<world-name>/viewer/terrain.glb
  -> outputs/<world-name>/viewer/index.html
```

## Components

### DEM Download

Module: `src/gz_terrain_gen/opentopo.py`

Responsibilities:

- Reads `OPENTOPOGRAPHY_API_KEY`.
- Uses CLI-provided or default center coordinates and area size.
- Calls the OpenTopography `globaldem` endpoint for COP30 data.
- Writes `outputs/<world-name>/dem.tif` by default.
- Records requested center, requested bounds, and DEM metadata in
  `outputs/<world-name>/metadata.json`.

### DEM Tiling

Module: `src/gz_terrain_gen/tiling.py`

Responsibilities:

- Reads `outputs/<world-name>/dem.tif` by default.
- Converts a 200 m tile size into latitude/longitude degree increments.
- Writes each tile to `outputs/<world-name>/tiles/tile_X_Y.tif`.
- Writes `outputs/<world-name>/tiles/tiles.csv` with tile bounds and Gazebo
  placement metadata.
- Records tile size, tile count, and manifest path in `metadata.json`.

Important contract:

- `tiles.csv` is the manifest used by all later stages.

### Mesh Generation

Module: `src/gz_terrain_gen/mesh.py`

Responsibilities:

- Reads `outputs/<world-name>/tiles/tiles.csv`.
- Opens `outputs/<world-name>/dem.tif` with rasterio.
- Samples the DEM using bilinear interpolation.
- Builds a local mesh for each tile where X/Y are tile-local meters and Z is
  DEM elevation.
- Writes `outputs/<world-name>/mesh/tile_X_Y.dae`.
- Records mesh count and mesh directory in `metadata.json`.

Important contract:

- Meshes are centered around local `(0, 0)` and later placed in Gazebo using the
  center coordinates from `tiles.csv`.

### Gazebo Generation

Module: `src/gz_terrain_gen/gazebo.py`

Responsibilities:

- Reads `outputs/<world-name>/mesh/*.dae`, `outputs/<world-name>/tiles/tiles.csv`, and
  `assets/texture/soil.jpg` by default.
- Adds flat normals and UVs to each Collada mesh.
- Creates one Gazebo model per terrain tile.
- Creates `outputs/<world-name>/gz/levels_terrain.sdf` with a level for each
  terrain tile.
- Creates `outputs/<world-name>/gz/single_tile_terrain.sdf` for simpler
  inspection.
- Creates a `level_probe` performer model and
  `outputs/<world-name>/gz/travel_levels.sh`.
- Records Gazebo output paths and model count in `metadata.json`.

Important contract:

- `gz sim --levels levels_terrain.sdf` uses the performer location to exercise
  Gazebo level loading.

### Browser Viewer

Module: `src/gz_terrain_gen/viewer.py`

Responsibilities:

- Reads `outputs/<world-name>/dem.tif` and `outputs/<world-name>/tiles/tiles.csv`.
- Rebuilds tile meshes using the same DEM sampling logic as mesh generation.
- Applies tile center offsets from `tiles.csv` so all tiles form one combined
  terrain.
- Writes `outputs/<world-name>/viewer/terrain.glb` and
  `outputs/<world-name>/viewer/index.html`.
- Provides `gz-terrain-gen-viewer` to serve the viewer with Python's built-in
  HTTP server.
- Records viewer output paths and combined vertex/face counts in
  `metadata.json`.

Important contract:

- The viewer is for mesh inspection only. Gazebo worlds, models, and level
  loading remain separate outputs.
- `index.html` uses Three.js from CDN, so browser access requires internet
  unless Three.js is vendored later.

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
  main.py
  cli.py
  opentopo.py
  tiling.py
  mesh.py
  metadata.py
  viewer.py
  gazebo.py
  paths.py
```

- A CLI command controls the whole pipeline.
- A second helper command serves the generated browser viewer.
- All paths are explicit and configurable.
- Generated artifacts go under `outputs/<world-name>/` or another configured
  output root.
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
