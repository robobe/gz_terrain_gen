# Refactor `run_pipeline` Into Pipeline Stages

Status: executed

## Summary

Refactor `run_pipeline` in `main.py` from one long method into a short
orchestrator plus focused stage functions. Preserve current generated files,
metadata updates, logs, final stdout output, and CLI behavior.

## Key Changes

- Added `DemStageResult`, `TileStageResult`, and `MeshStageResult`.
- Extracted stage execution functions for DEM preparation, tile splitting, mesh
  generation, Gazebo generation, and viewer generation.
- Extracted metadata recording functions for each stage.
- Extracted `print_pipeline_completion(...)` for final viewer command,
  metadata path, and completion summary output.
- Reduced `run_pipeline(...)` to an ordered orchestration function.

## Test Plan

Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "def prepare_dem|def split_tiles_stage|def generate_mesh_stage|def generate_gazebo_stage|def generate_viewer_stage|def print_pipeline_completion|def run_pipeline" src/gz_terrain_gen/main.py
test -f plans/017_refactor_run_pipeline_stages.md
git status --short
```

## Assumptions

- This is a behavior-preserving refactor.
- Stage functions stay in `main.py` because `main.py` owns application flow.
- Metadata dictionaries remain intentionally flexible.
- Failure-status metadata and reporter abstraction are separate follow-up
  refactors.

