# Development

This project is a `uv` managed Python package.

## Environment

Create or update the local virtual environment:

```bash
uv sync
```

Run commands through `uv run`:

```bash
uv run python --version
uv run gz-terrain-gen --help
uv run pytest
```

Activation is optional:

```bash
source .venv/bin/activate
```

## Tests

Run the test suite:

```bash
uv run pytest
```

Compile source and tests:

```bash
uv run python -m compileall -f src tests
```

## Dependencies

Python dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
Raster reads use `rasterio`; combined viewer export uses `trimesh` and
`pygltflib`. Verify core Python dependencies with:

```bash
uv run python -c "import rasterio, trimesh, pygltflib; print('deps ok')"
```

## Git

This repository tracks source, tests, docs, assets, plans, `pyproject.toml`, and
`uv.lock`.

Do not track:

- `.venv/`
- `.pytest_cache/`
- `__pycache__/`
- `*.pyc`
- `outputs/`

## Generated Output

Generated terrain artifacts should be written under `outputs/<world-name>/`:

```text
outputs/demo_world/
├── metadata.json
├── dem.tif
├── tiles/
├── mesh/
├── gz/
└── viewer/
```
