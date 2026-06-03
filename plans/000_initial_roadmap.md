# 000: Initial Codex Development Roadmap

## Status

superseded

## Date

2026-06-03

## Goal

Capture the original roadmap for turning the script pipeline into a
reproducible, configurable terrain generation tool.

## Original Roadmap

This plan is written so Codex can develop the project in small, reviewable
steps. Each task should finish with a runnable check and a short note about what
changed.

## Goal

Turn the current working terrain-generation scripts into a reproducible,
configurable tool for generating Gazebo terrain worlds from DEM data.

## Working Method With Codex

Use Codex in focused prompts. Good prompts should name the target file or stage,
state the desired behavior, and ask Codex to run verification.

Example:

```text
Refactor code/split_dem.py so it has a main() function and argparse options for
input DEM, output directory, and tile size. Keep current defaults. Run syntax
checks and a small test if possible.
```

Recommended loop:

1. Ask Codex to inspect the relevant code before editing.
2. Ask for one bounded change at a time.
3. Require a verification command for every change.
4. Review generated files before committing.
5. Keep generated DEM, mesh, and Gazebo outputs separate from source changes.

## Milestone 1: Project Hygiene

Tasks:

- Initialize git if this directory is meant to be version controlled.
- Add `.gitignore` for `__pycache__/`, virtual environments, downloaded DEMs,
  generated tiles, generated meshes, and generated Gazebo models.
- Add `requirements.txt` or `pyproject.toml`.
- Add a short setup section for Ubuntu/Gazebo/GDAL dependencies.
- Decide whether generated sample output should stay in the repo.

Verification:

```bash
python3 -m py_compile code/*.py
```

## Milestone 2: Make Scripts Reproducible

Tasks:

- Add `main()` and `argparse` to each script.
- Keep current defaults so existing behavior still works.
- Make all input and output paths explicit.
- Fix the DEM download output path so it writes to `data/dem_1km.tif` by default.
- Add clear error messages for missing API key, missing DEM, missing texture, and
  missing tile manifest.

Verification:

```bash
cd code
python3 split_dem.py --help
python3 tiles_to_dae.py --help
python3 create_gz_level_models.py --help
```

## Milestone 3: Extract Testable Logic

Tasks:

- Move pure functions into importable modules.
- Keep command-line entry scripts thin.
- Add tests for tile manifest generation.
- Add tests for DEM sampling edge cases.
- Add tests for mesh vertex/face counts.
- Add tests for generated SDF containing expected models and levels.

Verification:

```bash
python3 -m pytest
```

## Milestone 4: Improve Terrain Quality

Tasks:

- Add options for height offset and vertical scale.
- Add optional mesh simplification or fixed output resolution.
- Generate real normals instead of flat upward normals.
- Make texture path configurable.
- Consider per-tile texture coordinates that repeat at a configurable scale.

Verification:

- Generate a small test world.
- Open `gz/single_tile_terrain.sdf` for visual inspection.
- Run `gz sim --levels levels_terrain.sdf` and move the probe through levels.

## Milestone 5: Package A CLI

Tasks:

- Create a package layout.
- Add a single CLI, for example:

```bash
gz-terrain-gen download --config terrain.toml
gz-terrain-gen split --config terrain.toml
gz-terrain-gen mesh --config terrain.toml
gz-terrain-gen gazebo --config terrain.toml
gz-terrain-gen all --config terrain.toml
```

- Add example configs.
- Add documentation for common workflows.

Verification:

```bash
gz-terrain-gen --help
gz-terrain-gen all --config examples/terrain.toml
```

## Milestone 6: Gazebo Behavior Checks

Tasks:

- Confirm the SDF level plugin format against the Gazebo version in use.
- Add a generated world for one tile and another for all levels.
- Add a script that verifies expected model paths and SDF files exist.
- Document how to use `GZ_SIM_RESOURCE_PATH`.

Verification:

```bash
cd code/gz
export GZ_SIM_RESOURCE_PATH=$PWD/models
gz sim --levels levels_terrain.sdf
./travel_levels.sh
```

## First Codex Prompt To Use Next

```text
Review the repository and implement Milestone 1 from this roadmap. Add
.gitignore and dependency documentation only. Do not refactor Python yet. Run
py_compile after the change.
```
