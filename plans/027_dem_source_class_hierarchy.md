# Add DEM Source Class Hierarchy

Status: executed

## Summary

Refactored DEM preparation out of `main.py` into a dedicated DEM source model.
Added a class hierarchy for DEM providers with OpenTopography and local GeoTIFF
implementations.

## Key Changes

- Added `src/gz_terrain_gen/dem_source.py`.
- Added `DemSource`, `DemSourceResult`, `OpenTopographyDemSource`, and
  `LocalFileDemSource`.
- Updated `main.py` to select a source through `dem_source_from_config(...)`.
- Kept existing CLI behavior: `--dem-file` selects local file, otherwise
  OpenTopography.
- Added `docs/dem_source.md` with the class hierarchy and extension guidance.

## Verification

Planned checks:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
test -f docs/dem_source.md
test -f plans/027_dem_source_class_hierarchy.md
rg -n "class DemSource|OpenTopographyDemSource|LocalFileDemSource|DemSourceResult|dem_source_from_config" src tests docs
git status --short
```
