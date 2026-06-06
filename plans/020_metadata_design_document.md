# Add Application Metadata Design Document

Status: executed

## Summary

Created a design document under `docs/` that explains the application metadata
model without focusing on the generated metadata file. The document shows the
metadata classes as an in-memory application model and includes a simple Mermaid
class diagram.

## Key Changes

- Added `docs/metadata_design.md`.
- Documented `MetadataDocument` as the root metadata object.
- Documented request, DEM, tile, mesh, Gazebo, and viewer metadata sections.
- Added a Mermaid class diagram with containment arrows only.
- Documented `center_height_m` as a planned derived value, not yet
  implemented.

## Verification

Planned checks:

```bash
test -f docs/metadata_design.md
test -f plans/020_metadata_design_document.md
rg -n "classDiagram|MetadataDocument|center_height_m|world_name|tile_m|minimum_m|maximum_m" docs/metadata_design.md
git status --short
```
