# Gazebo Usage

The Gazebo stage creates model folders, worlds, and a travel script under
`outputs/<world-name>/gz/`. Generated worlds embed the GUI template from
`src/templates/gz_gui.xml` with a top-down camera above the first tile and
performer start position.

## Generate Gazebo Files

Run the full terrain pipeline:

```bash
export OPENTOPOGRAPHY_API_KEY=your_api_key
uv run gz-terrain-gen --world-name demo_world
```

Or use an existing GeoTIFF DEM without an OpenTopography API key:

```bash
uv run gz-terrain-gen --world-name demo_world --dem-file /path/to/dem.tif
```

Configure the Z size of each Gazebo level geometry box when needed:

```bash
uv run gz-terrain-gen --world-name demo_world --level-z-size-m 1500
```

## Run The Level World

From the generated Gazebo directory:

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

## Generated Files

```text
outputs/demo_world/gz/
├── levels_terrain.sdf
├── single_tile_terrain.sdf
├── travel_levels.sh
└── models/
```

`levels_terrain.sdf` contains one Gazebo level per terrain tile. The
`level_probe` performer model is moved through the tile centers by
`travel_levels.sh` to exercise level load and unload behavior.

The generated `level_probe` starts 30 m above the first terrain tile center.
The embedded GUI camera starts 100 m above the same point and looks straight
down. Level geometry X/Y size follows each tile size; level geometry Z size
defaults to 1500 m and is configurable with `--level-z-size-m`.

Without `--levels`, Gazebo loads every model at startup, so level load/unload
behavior is not exercised.

Rerun `uv run gz-terrain-gen --world-name <name>` to regenerate SDF files after
changing the GUI template or camera logic.
