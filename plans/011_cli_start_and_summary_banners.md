# Add Start And Completion CLI Banners

Status: executed

## Summary

Add human-readable CLI banners at the start and end of `gz-terrain-gen`.
The start banner shows application version, world name, and output location.
The completion banner summarizes the generated terrain result from metadata.

## Key Changes

- Add CLI reporting helpers that format banners with `click.echo`.
- Print the start banner after output-folder confirmation and before pipeline
  work starts.
- Print the completion summary after all metadata sections are written.
- Use `gz_terrain_gen.__version__` as the version source.
- Keep existing stage progress messages.

## Test Plan

- Test start banner content.
- Test completion summary content.
- Test CLI invocation with monkeypatched pipeline prints the start banner.
- Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "Generation Summary|GZ Terrain Generator|Version:" src tests docs
git status --short
```

## Assumptions

- Banners are stdout output.
- Area is displayed as `size_km x size_km`.
- Existing generated files under `outputs/` are not updated until the pipeline
  is rerun.

## Execution Results

- Added start and completion banner formatting helpers.
- CLI now prints the start banner after output-folder reset confirmation and
  before pipeline work.
- CLI now prints the completion summary after final metadata update.
- Added unit tests for banner formatting and CLI start banner output.
- Verification passed:
  - `uv run pytest`
  - `uv run python -m compileall -f src tests`
  - `uv run gz-terrain-gen --help`
