# 005: Migrate CLI From argparse To Click

## Status

executed

## Date

2026-06-03

## Goal

Replace the current `argparse` CLI implementation with Click while preserving
the existing command names, options, required `--world-name`, metadata updates,
and generated output behavior.

## Planned Changes

- Add `click` as a direct runtime dependency.
- Rewrite `src/gz_terrain_gen/cli.py` with a Click group and subcommands.
- Preserve all current command options and defaults.
- Use Click validation for world names.
- Replace parser tests with `click.testing.CliRunner` tests.
- Update `AGENTS.md` so future CLI work uses Click and avoids `argparse`.

## Verification Plan

```bash
uv add click
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run gz-terrain-gen all --help
uv run gz-terrain-gen split --world-name test_world --help
uv run python -c "import click; print(click.__version__)"
rg -n "argparse" src tests AGENTS.md docs README.md
test -f plans/005_migrate_cli_to_click.md
git status --short
```

## Execution Result

Executed in this change.

Verification passed:

```bash
uv add click
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run gz-terrain-gen all --help
uv run gz-terrain-gen split --world-name test_world --help
uv run python -c "import click; print(click.__version__)"
rg -n "argparse" src tests AGENTS.md docs README.md
test -f plans/005_migrate_cli_to_click.md
```

Results:

- Tests passed: 15 passed.
- Source and tests compiled successfully.
- CLI help works through Click.
- No stale standard-library parser references remain in source, tests, docs, or
  agent instructions.
- `click` is a direct dependency.

## Follow-Up Notes

- This is a CLI framework migration only.
- No generated artifact layout or metadata schema changes are intended.
