# Add Existing DEM File CLI Option

Status: executed

## Summary

Add a CLI option that lets the pipeline use an existing GeoTIFF DEM instead of
downloading from OpenTopography. The app copies the file into the world output
as `dem.tif` and continues with the normal pipeline.

## Key Changes

- Add `--dem-file /path/to/existing.tif`.
- Skip OpenTopography download when `--dem-file` is provided.
- Copy the existing DEM to `outputs/<world-name>/dem.tif`.
- Record DEM source metadata as either `local_file` with `source_path` or
  `opentopography`.
- Update docs and tests.

## Test Plan

- Verify CLI help includes `--dem-file`.
- Verify local DEM mode skips `download_dem`.
- Verify local DEM mode copies the file to world output.
- Verify metadata records `source` and `source_path`.
- Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "dem-file|local_file|source_path" src tests README.md docs plans
git status --short
```

## Assumptions

- Input DEM is a readable GeoTIFF.
- The pipeline still uses `outputs/<world-name>/dem.tif` after copying.
- Existing output-folder reset confirmation still runs before copying.

## Execution Results

- Added `--dem-file` to the main CLI.
- Local DEM mode copies the provided GeoTIFF to `outputs/<world-name>/dem.tif`
  and skips OpenTopography download.
- Metadata records `source: local_file` and `source_path` when a local DEM is
  used.
- Documentation and tests were updated.
- Verification passed:
  - `uv run pytest`
  - `uv run python -m compileall -f src tests`
  - `uv run gz-terrain-gen --help`
