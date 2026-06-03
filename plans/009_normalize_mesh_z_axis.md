# Normalize Meshes To Gazebo Z Zero

Status: executed

## Summary

Normalize generated terrain mesh elevations so the minimum valid DEM elevation
becomes Gazebo Z `0`. Record the normalization in metadata.

## Key Changes

- Compute the minimum valid DEM elevation when opening the DEM for mesh
  generation.
- Subtract that elevation from every generated mesh vertex Z value.
- Apply the same normalized mesh logic to the browser viewer, since it reuses
  mesh generation.
- Add mesh metadata fields indicating Z-axis normalization and the elevation
  offset used.
- Update docs and tests.

## Test Plan

- Verify generated mesh vertices have minimum Z `0`.
- Verify viewer combined mesh has minimum Z `0`.
- Verify mesh metadata includes the normalization flag and offset.
- Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
```

## Assumptions

- Normalization is always enabled.
- The offset is the minimum valid DEM elevation before normalization.
- Generated outputs should be recreated by rerunning the pipeline.

## Execution Results

- Mesh vertices now subtract the minimum valid DEM elevation.
- Browser viewer terrain uses the same normalized mesh logic.
- Mesh metadata records `normalized_to_gazebo_z_zero` and `z_offset_m`.
- Documentation and tests were updated.
- Verification passed:
  - `uv run pytest`
  - `uv run python -m compileall -f src tests`
