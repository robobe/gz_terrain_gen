# Replace Pipeline `click.echo` Stage Messages With Logs

Status: executed

## Summary

Replace stage-progress `click.echo` calls inside the pipeline with Loguru log
messages, so pipeline execution no longer mixes routine progress reporting with
user-facing CLI output.

## Key Changes

- Replaced progress output for DEM, tiling, mesh, Gazebo, and viewer stages
  with `logger.info(...)`.
- Kept start and completion banners on stdout.
- Kept final viewer serve command and metadata path on stdout.
- Left the viewer helper CLI output unchanged because it is a separate command.

## Test Plan

Run:

```bash
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
rg -n "click.echo" src/gz_terrain_gen/main.py
test -f plans/018_replace_pipeline_echo_with_logs.md
git status --short
```

## Assumptions

- Logs remain stderr through Loguru.
- Final human summary remains stdout.
- This reduces CLI coupling but does not introduce a reporter abstraction yet.

