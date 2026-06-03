# 003: Reorganize Project Markdown And Add Agent Instructions

## Status

executed

## Date

2026-06-03

## Goal

Move long-form project documentation out of the repository root, add
`AGENTS.md` for coding-agent rules, and keep `plans/` as the place for plan
records.

## Planned Changes

- Move the misspelled root architecture document to `docs/architecture.md`.
- Move the root roadmap document to `plans/000_initial_roadmap.md`.
- Add `docs/development.md`.
- Add `docs/gazebo.md`.
- Add root `AGENTS.md`.
- Update `README.md` to link to the new documentation locations.

## Verification Plan

```bash
uv run pytest
uv run python -m compileall -f src tests
test -f AGENTS.md
test -f docs/architecture.md
test -f docs/development.md
test -f docs/gazebo.md
test -f plans/000_initial_roadmap.md
test ! -f <old root architecture document>
test ! -f <old root roadmap document>
rg active docs for stale root-document references
git status --short
```

## Execution Result

Executed in this change. Verification results are recorded in the assistant
response for this turn.

## Follow-Up Notes

- Future plans should be saved before execution and updated after execution.
- `AGENTS.md` is now the root instruction file for coding agents.
