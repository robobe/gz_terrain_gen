# Agent Instructions

These rules apply to coding agents working in this repository.

## Workflow

- Inspect relevant files before editing.
- Prefer `rg` for searching.
- Use `uv run` for Python commands.
- Keep source changes under `src/gz_terrain_gen/` unless documentation, tests, or
  assets are explicitly involved.
- Keep generated terrain artifacts under `outputs/`.
- Do not commit `.venv/`, caches, `__pycache__/`, `.pyc` files, or generated
  terrain outputs.

## Plans

- Save every proposed or received plan in `plans/`, even if it is not executed.
- Use the next numbered Markdown filename.
- If a plan is later executed, update the same plan file with execution results
  instead of creating a duplicate.
- Follow the format described in `plans/README.md`.

## Verification

Run relevant checks before finalizing changes. For normal source or docs work,
use:

```bash
uv run pytest
uv run python -m compileall -f src tests
```

For CLI changes, also check:

```bash
uv run gz-terrain-gen --help
```

## CLI Conventions

- Use Click for all CLI code.
- Do not use the standard-library argument parser for CLI code.
- Keep Click command functions thin.
- Keep core behavior in importable modules outside the CLI layer.
- Use Click options for validation, defaults, help text, and path arguments.
- For CLI changes, verify top-level and affected subcommand help.

## Logging Conventions

- Use Loguru for application logging.
- Configure logging in the CLI entrypoint.
- Log format must include module name and line number.
- Keep `click.echo` for user-facing command result summaries.
- Do not log secrets, API keys, or credential values.

## Python Module Conventions

- Every Python module should start with a short module docstring.
- The docstring should explain the module's responsibility in one or two
  sentences.
- Keep module docstrings practical; do not turn them into long design
  documents.
- If a module maps to a documented diagram, include a relative Markdown-style
  reference in the docstring text, for example:

```python
"""Pipeline orchestration for terrain generation.

See docs/application_flow.md for the application block flow.
"""
```

- Prefer links to stable docs such as `docs/application_flow.md`,
  `docs/metadata_design.md`, and `docs/architecture.md`.
- Do not link module docstrings to generated files under `outputs/`.
- Put the module docstring before imports. If the module uses
  `from __future__ import ...`, keep the future import first and put the
  docstring immediately after it.

## Data Shape Conventions

- Use `@dataclass(frozen=True)` for fixed-shape internal application data.
- Prefer attribute access such as `paths.dem` over dictionary access such as
  `paths["dem"]`.
- Avoid dictionaries for known structures such as path bundles, parsed config,
  stage results, and typed generation outputs.
- Use dictionaries for dynamic JSON-like data, external API payloads, and
  metadata files where the key shape is intentionally flexible.
- Keep dataclasses small, explicit, and importable from the module that owns the
  concept.

## Project Conventions

- The CLI entrypoint is `gz-terrain-gen`, defined as `gz_terrain_gen.main:main`.
- `cli.py` parses and validates command arguments; `main.py` owns application
  flow and pipeline execution.
- Runtime dependencies are managed in `pyproject.toml` and locked in `uv.lock`.
- The default generated artifact root is `outputs/`.
- The default texture asset is `assets/texture/soil.jpg`.
- Gazebo itself remains a system dependency.

## Preferred Libraries

- CLI: Click
- Tests: pytest
- Arrays/math: numpy
- Raster/GeoTIFF: rasterio
- Browser mesh viewer/export: trimesh and pygltflib
- HTTP: requests
- Logging: Loguru

## String Constants

- Avoid repeated free string literals in Python modules.
- Put stable filenames, model names, XML tag names, plugin names, and external identifiers
  in module-level constants directly below imports.
- Use uppercase constant names, for example `LEVELS_TERRAIN_SDF = "levels_terrain.sdf"`.
- Do not convert one-off human-readable messages, docstrings, or large XML templates unless
  doing so improves clarity.