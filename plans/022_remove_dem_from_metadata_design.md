# Remove DEM From Metadata Design

Status: executed

## Summary

Updated `docs/metadata_design.md` to remove `DemMetadata` from the simplified
application metadata design.

## Key Changes

- Removed `DemMetadata` from the Mermaid class diagram.
- Removed `DemMetadata` containment arrows.
- Reworded main values so world location and elevation are represented by
  `GeoBounds`, `GeoCenter`, and `ElevationStats`.
- Removed the `DemMetadata` class note.

## Verification

Planned checks:

```bash
rg -n "DemMetadata" docs/metadata_design.md
rg -n "classDiagram|MetadataDocument|GeoBounds|GeoCenter|ElevationStats|TileMetadata|MeshMetadata" docs/metadata_design.md
git status --short
```
