# Add Application Block Diagram And Flow Document

Status: executed

## Summary

Created a new documentation page that shows the full terrain-generation
application as a Mermaid block/flow diagram.

## Key Changes

- Added `docs/application_flow.md`.
- Documented the flow from CLI input through DEM preparation, tiling, mesh
  generation, Gazebo output, browser viewer output, metadata, and final outputs.
- Added short summaries for each application block.
- Added the current execution order.

## Verification

Planned checks:

```bash
test -f docs/application_flow.md
test -f plans/025_application_block_flow_diagram.md
rg -n "flowchart|CLI|Main Orchestrator|DEM Preparation|DEM Tiling|Mesh Generation|Gazebo Generation|Viewer Generation|Metadata Request|Outputs|Execution Order" docs/application_flow.md
git status --short
```
