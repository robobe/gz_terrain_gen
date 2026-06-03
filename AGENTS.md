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

## Project Conventions

- The CLI entrypoint is `gz-terrain-gen`.
- Runtime dependencies are managed in `pyproject.toml` and locked in `uv.lock`.
- The default generated artifact root is `outputs/`.
- The default texture asset is `assets/texture/soil.jpg`.
- Gazebo itself remains a system dependency.
