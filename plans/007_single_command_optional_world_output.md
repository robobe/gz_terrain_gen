# 007: Single Command Optional World Output

## Status

executed

## Date

2026-06-03

## Goal

Make the application run the complete terrain generation pipeline from one
command, make `--world-name` optional with a default, rename the default DEM file
to `dem.tif`, and confirm before removing an existing world output folder.

## Planned Changes

- Remove public stage subcommands from the CLI.
- Add `src/gz_terrain_gen/main.py` as the package entrypoint.
- Point the console script at `gz_terrain_gen.main:main`.
- Make `--world-name` optional with default `terrain_world`.
- Change default DEM path to `outputs/<world-name>/dem.tif`.
- Prompt before deleting an existing world output folder.
- Update tests and docs for the single-command workflow.

## Verification Plan

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run gz-terrain-gen --world-name test_world --help
uv run python -c "from gz_terrain_gen.main import main; print(callable(main))"
rg -n "dem_1km|download|split|mesh|gazebo|all" README.md docs src/gz_terrain_gen/cli.py tests/test_cli.py
test -f plans/007_single_command_optional_world_output.md
git status --short
```

## Execution Result

Executed in this change.

Verification passed:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run gz-terrain-gen --world-name test_world --help
uv run python -c "from gz_terrain_gen.main import main; print(callable(main))"
rg -n "dem_1km" README.md docs src tests
rg -n "uv run gz-terrain-gen (download|split|mesh|gazebo|all)|Commands:|Missing option '--world-name'" README.md docs src/gz_terrain_gen/cli.py tests/test_cli.py
test -f plans/007_single_command_optional_world_output.md
```

Results:

- Tests passed.
- Source and tests compiled successfully.
- Console script help shows the single-command interface.
- `gz_terrain_gen.main.main` imports and is callable.
- No stale `dem_1km.tif` references remain.
- No stale public subcommand usage remains.

## Follow-Up Notes

- Existing output folders are removed only after interactive confirmation.
- No `--force` option is included in this version.
