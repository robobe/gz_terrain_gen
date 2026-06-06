# Remove Gazebo And Viewer From Metadata Design

Status: executed

## Summary

Updated `docs/metadata_design.md` to keep the application metadata design focused
on world, request, DEM, tile, and mesh metadata.

## Key Changes

- Removed `GazeboMetadata` from the Mermaid class diagram.
- Removed `ViewerMetadata` from the Mermaid class diagram.
- Removed Gazebo/viewer output path references from the main values section.
- Removed Gazebo/viewer class notes.

## Verification

Planned checks:

```bash
rg -n "GazeboMetadata|ViewerMetadata" docs/metadata_design.md
rg -n "classDiagram|MetadataDocument|GeoBounds|ElevationStats|TileMetadata|MeshMetadata" docs/metadata_design.md
git status --short
```
