# Move Application Flow From CLI To Main

Status: executed

## Summary

Refactor the app so `cli.py` only defines and parses Click options, while
`main.py` owns logging setup, output reset confirmation, banners, pipeline
stages, completion summary, and final return.

## Key Changes

- Added `TerrainGenerationConfig` as the typed CLI parse result.
- Changed the Click callback to return configuration instead of running the
  terrain pipeline.
- Moved pipeline orchestration and application-flow helpers into `main.py`.
- Moved default world path resolution into `paths.py` and re-exported it from
  `cli.py` for compatibility.
- Preserved the public `gz-terrain-gen` command and existing options.

## Test Plan

- Verify CLI help and validation still work.
- Verify CLI parsing returns `TerrainGenerationConfig`.
- Verify `main.main()` parses args and runs application flow.
- Verify output-folder confirmation still aborts or removes before pipeline
  execution.
- Verify local DEM pipeline mode still skips download and copies the DEM.
- Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run python -c "from gz_terrain_gen.main import main, run_pipeline; print(callable(main), callable(run_pipeline))"
rg -n "run_pipeline|TerrainGenerationConfig|reset_existing_world_output" src tests
git status --short
```

## Assumptions

- `cli.py` should parse and validate only.
- `main.py` should be the single place that owns application flow.
- Public command behavior should not change.
- The viewer CLI in `viewer.py` is out of scope.

