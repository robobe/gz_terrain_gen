# Gazebo Usage

The Gazebo stage creates model folders, worlds, and a travel script under
`outputs/gz/`.

## Generate Gazebo Files

Run the full terrain pipeline:

```bash
export OPENTOPOGRAPHY_API_KEY=your_api_key
uv run gz-terrain-gen all
```

Or run only the Gazebo stage after DEM, tiles, and meshes already exist:

```bash
uv run gz-terrain-gen gazebo
```

## Run The Level World

From the generated Gazebo directory:

```bash
cd outputs/gz
export GZ_SIM_RESOURCE_PATH=$PWD/models
gz sim --levels levels_terrain.sdf
```

In a second terminal:

```bash
cd outputs/gz
./travel_levels.sh
```

## Generated Files

```text
outputs/gz/
├── levels_terrain.sdf
├── single_tile_terrain.sdf
├── travel_levels.sh
└── models/
```

`levels_terrain.sdf` contains one Gazebo level per terrain tile. The
`level_probe` performer model is moved through the tile centers by
`travel_levels.sh` to exercise level load and unload behavior.

Without `--levels`, Gazebo loads every model at startup, so level load/unload
behavior is not exercised.
