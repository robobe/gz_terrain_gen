# Convert Metadata Dictionaries To Dataclasses

Status: executed

## Summary

Refactor `src/gz_terrain_gen/metadata.py` so fixed metadata shapes are represented by frozen dataclasses, including the top-level metadata document. Preserve the existing `metadata.json` file format and keys, while moving internal code away from magic string dictionary access.

## Key Changes

- Added frozen dataclasses for metadata sections and the top-level `MetadataDocument`.
- Added `MetadataUpdate` for partial stage metadata writes.
- Updated metadata helpers to return dataclasses and serialize to the existing JSON shape at the file boundary.
- Updated application code to pass `MetadataUpdate` and read completion summary values through attributes.
- Moved Gazebo/viewer result imports behind `TYPE_CHECKING` to reduce runtime import coupling.

## Verification

Planned verification:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "metadata\\[|request_metadata\\[|data\\[\\\"schema_version\\\"\\]" src tests
test -f plans/019_metadata_dataclasses.md
git status --short
```
