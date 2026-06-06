# Align Metadata Design Text With Current Diagram

Status: executed

## Summary

Updated `docs/metadata_design.md` text so it describes only the classes and
fields currently shown in its Mermaid diagram. The diagram was left unchanged
and treated as the source of truth.

## Key Changes

- Removed stale references to output path fields, `GeoCenter`, and
  `center_height_m`.
- Updated main values to describe `world_name`, requested center, square area,
  bounding box, elevation stats, tile size/count, mesh count, and Z
  normalization.
- Updated class notes so they match the current diagram.

## Verification

Planned checks:

```bash
test -f docs/metadata_design.md
rg -n "GeoCenter|center_height_m|tiles_dir|mesh_dir|manifest|DEM source" docs/metadata_design.md
rg -n "world_name|center_lat|center_lon|size_km|GeoBounds|ElevationStats|tile_m|normalized_to_gazebo_z_zero|z_offset_m" docs/metadata_design.md
test -f plans/023_align_metadata_design_text_with_diagram.md
git status --short
```
