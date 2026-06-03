# 001: Convert To uv Python Project

## Goal

Convert the repository from script-based Python files into a `uv` managed Python
project with an installable package and CLI.

## Changes Made

- Added `pyproject.toml` and `uv.lock`.
- Created the `src/gz_terrain_gen/` package.
- Added the `gz-terrain-gen` CLI with `download`, `split`, `mesh`, `gazebo`, and
  `all` subcommands.
- Moved source logic into package modules.
- Moved the soil texture asset to `assets/texture/soil.jpg`.
- Added tests under `tests/`.
- Updated README and architecture documentation.
- Configured `.venv/` and generated outputs to stay out of source control.

## Verification

Commands run:

```bash
uv sync --python /usr/bin/python3
uv run gz-terrain-gen --help
uv run python -m compileall -f src tests
uv run python -c "from osgeo import gdal; print(gdal.VersionInfo())"
uv run pytest
```

Result:

- Python environment synced with Python 3.12.3.
- CLI help loaded successfully.
- GDAL binding imported successfully.
- Tests passed: 4 passed.

## Follow-Up Notes

- Generated terrain artifacts should go under `outputs/`.
- The mesh stage currently depends on `GDAL==3.8.4`, matching this machine's
  system GDAL version.
- Future cleanup can replace `osgeo.gdal` usage with `rasterio` only.
