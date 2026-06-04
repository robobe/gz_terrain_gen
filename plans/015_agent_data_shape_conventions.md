# Add Data Shape Conventions To AGENTS.md

Status: executed

## Summary

Update `AGENTS.md` so future agents use dataclasses for fixed internal data
shapes instead of dictionaries with magic string keys. Also correct the stale
project convention about `main.py` and `cli.py`.

## Key Changes

- Added `Data Shape Conventions` to prefer `@dataclass(frozen=True)` for fixed
  internal application data.
- Documented attribute access, such as `paths.dem`, as preferred over magic
  string dictionary access for known structures.
- Clarified that dictionaries remain appropriate for dynamic JSON-like data,
  external API payloads, and flexible metadata files.
- Updated the project convention so `cli.py` parses arguments and `main.py`
  owns application flow and pipeline execution.

## Test Plan

Run:

```bash
test -f AGENTS.md
rg -n "Data Shape Conventions|dataclass|main.py owns application flow|delegates to the Click app" AGENTS.md
test -f plans/015_agent_data_shape_conventions.md
git status --short
```

## Assumptions

- This is a documentation-only change.
- No Python source behavior changes are needed.
- The actual `WorldPaths` dataclass refactor should be a separate follow-up
  plan.

