# Enforce Gazebo String Constants

Status: executed

## Date

2026-06-06

## Goal

Apply the `AGENTS.md` string constants rule to `src/gz_terrain_gen/gazebo.py`.

## Planned Changes

- Move stable filenames, directory names, model names, manifest keys, XML tags,
  plugin identifiers, and similar external identifiers into module-level
  constants directly below imports.
- Keep large XML templates, docstrings, and one-off human-readable messages
  inline unless extracting them improves clarity.
- Update references in `gazebo.py` to use the new constants.

## Verification Plan

```bash
uv run pytest
uv run python -m compileall -f src tests
```

## Execution Result

- Added module-level constants in `src/gz_terrain_gen/gazebo.py` for stable
  generated filenames, model directories, manifest keys, Collada selectors and
  attributes, model names, URI prefixes, and related identifiers.
- Updated Gazebo generation code to use the constants and explicit UTF-8
  encoding for generated text files.
- Added a focused `tests/test_gazebo.py` check that fails if selected stable
  identifiers are repeated as inline string literals in `gazebo.py`.
- Verified with:

```bash
uv run pytest
uv run python -m compileall -f src tests
```

## Follow-Up Notes

None.
