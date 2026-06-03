# Add Auto Top-Down Gazebo GUI Camera

Status: executed

## Summary

Embed `src/templates/gz_gui.xml` into generated Gazebo worlds and replace the
`MinimalScene` `camera_pose` with an auto-computed top-down camera. The camera
is located above the performer start location and high enough to see the
normalized terrain.

## Key Changes

- Render the GUI template during Gazebo SDF generation.
- Insert the GUI block before the sun light in both generated worlds.
- Add the Gazebo rendering system plugin.
- Compute camera X/Y from the first tile center and camera Z from normalized
  mesh elevation plus size-based clearance.
- Keep generated files under `outputs/` as outputs only; rerun the pipeline to
  update them.

## Test Plan

- Verify rendered GUI contains `MinimalScene` and replaces `camera_pose`.
- Verify both generated SDF strings contain GUI before the sun light.
- Verify camera pose uses first tile X/Y and Z above maximum mesh elevation.
- Verify generated SDF includes the rendering plugin.
- Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "MinimalScene|camera_pose|gz-sim-rendering-system|<gui" src tests docs
```

## Assumptions

- “Above the light tag” means insert the GUI XML before `<light name="sun">`.
- Camera X/Y should be above the performer start location.
- Camera should point straight down.
- Both generated Gazebo worlds should receive the GUI section.

## Execution Results

- Gazebo SDF generation now renders `src/templates/gz_gui.xml`.
- `MinimalScene` `camera_pose` is replaced with an auto top-down pose.
- Both generated worlds include GUI before the sun light and include the
  rendering system plugin.
- Camera height is based on normalized mesh elevation and terrain footprint.
- Verification passed:
  - `uv run pytest`
  - `uv run python -m compileall -f src tests`
  - `uv run gz-terrain-gen --help`
