# Refactor Fixed Data Shapes To Dataclasses

Status: executed

## Summary

Refactor fixed-shape internal dictionaries to frozen dataclasses, matching the
data shape convention in `AGENTS.md`. Keep intentionally flexible metadata JSON
dictionaries unchanged.

## Key Changes

- Added `WorldPaths` in `paths.py` and changed `default_paths(...)` to return it.
- Updated application code and tests from `paths["field"]` to `paths.field`.
- Added `GazeboGenerationResult` for Gazebo generation output.
- Added `ViewerGenerationResult` for browser viewer generation output.
- Updated metadata builders to accept the typed generation result objects.
- Left metadata JSON dictionaries and CSV manifest row dictionaries unchanged.

## Test Plan

Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run python -c "from gz_terrain_gen.paths import WorldPaths, default_paths; print(default_paths.__name__, WorldPaths.__name__)"
rg -n "paths\\[|viewer_info\\[|gazebo_info\\[" src tests
test -f plans/016_refactor_fixed_data_shapes_to_dataclasses.md
git status --short
```

## Assumptions

- CLI behavior and generated artifact layout stay unchanged.
- Metadata files stay JSON/dictionary based.
- CSV manifest row dataclasses are out of scope.
- `TerrainGenerationConfig` already follows the convention.

