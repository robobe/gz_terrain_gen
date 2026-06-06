# Update Application Metadata Usage To New Shape

Status: executed

## Summary

Updated the application metadata model and pipeline usage to match the current
`docs/metadata_design.md` Mermaid diagram. Runtime metadata now contains only
root document fields plus `request`, `tiles`, and `mesh` sections.

## Key Changes

- Removed DEM, Gazebo, and viewer metadata section dataclasses and helper
  functions.
- Moved elevation statistics into `RequestMetadata`.
- Reduced tile metadata to tile size and tile count.
- Reduced mesh metadata to mesh count and Z normalization.
- Kept Gazebo and viewer generation unchanged, but stopped recording them in
  application metadata.
- Updated completion summary to use only the new metadata shape.

## Verification

Planned checks:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "DemMetadata|GazeboMetadata|ViewerMetadata|dem_metadata|gazebo_metadata|viewer_metadata" src tests
rg -n "\"dem\"|\"gazebo\"|\"viewer\"" tests/test_metadata.py tests/test_cli.py
test -f plans/024_update_application_metadata_usage_to_new_shape.md
git status --short
```
