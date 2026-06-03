# 006: Add Loguru Application Logging

## Status

executed

## Date

2026-06-03

## Goal

Add Loguru application logging configured by the Click CLI with a global
`--log-level` option. The log format must include module name and line number.

## Planned Changes

- Add `loguru` as a direct runtime dependency.
- Add `src/gz_terrain_gen/log_config.py`.
- Configure Loguru from the CLI entrypoint.
- Add global `--log-level` with `DEBUG`, `INFO`, `WARNING`, and `ERROR`.
- Add stage-level info/debug logging without logging secrets.
- Update `AGENTS.md` logging conventions.
- Add tests for log format and CLI log-level behavior.

## Verification Plan

```bash
uv add loguru
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run gz-terrain-gen --log-level DEBUG split --world-name test_world --help
uv run python -c "from loguru import logger; print(logger)"
rg -n "LOG_FORMAT|loguru|--log-level" src tests AGENTS.md docs README.md
test -f plans/006_add_loguru_logging.md
git status --short
```

## Execution Result

Executed in this change.

Verification passed:

```bash
uv add loguru
uv run pytest
uv run python -m compileall -f src tests
uv run gz-terrain-gen --help
uv run gz-terrain-gen --log-level DEBUG split --world-name test_world --help
uv run python -c "from loguru import logger; print(logger)"
rg -n "LOG_FORMAT|loguru|--log-level" src tests AGENTS.md docs README.md
test -f plans/006_add_loguru_logging.md
```

Results:

- Tests passed: 20 passed.
- Source and tests compiled successfully.
- CLI help shows `--log-level`.
- Loguru import succeeded.
- `LOG_FORMAT` includes module name and line number.

## Follow-Up Notes

- Logs go to stderr only.
- `click.echo` remains for user-facing command summaries.
