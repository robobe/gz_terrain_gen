# 004: Add World-Named Output Folders And Metadata

## Status

executed

## Date

2026-06-03

## Goal

Add a required `--world-name` CLI option, write generated artifacts under
`outputs/<world-name>/`, use the world name in generated Gazebo worlds, and
write `metadata.json` describing the requested area and generated artifacts.

## Planned Changes

- Require `--world-name` on every CLI subcommand.
- Validate world names with `^[A-Za-z0-9][A-Za-z0-9_-]*$`.
- Resolve default paths under `outputs/<world-name>/`.
- Add JSON metadata with request, DEM, elevation, tile, mesh, and Gazebo details.
- Use the world name in generated SDF and travel script defaults.
- Update tests and documentation.

## Verification Plan

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen all --help
uv run gz-terrain-gen split --world-name test_world --help
test -f plans/004_world_name_output_and_metadata.md
rg -n "outputs/gz|dem_mesh_levels" README.md docs src tests
```

## Execution Result

Executed in this change.

Verification passed:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen all --help
uv run gz-terrain-gen split --world-name test_world --help
test -f plans/004_world_name_output_and_metadata.md
rg -n "outputs/gz|dem_mesh_levels" README.md docs src tests
```

Results:

- Tests passed: 12 passed.
- Source and tests compiled successfully.
- CLI help shows required `--world-name`.
- No stale `outputs/gz` or `dem_mesh_levels` references remain in README, docs,
  source, or tests.

## Follow-Up Notes

- `--output-dir` remains the root output directory.
- Explicit stage path flags remain available as overrides.
