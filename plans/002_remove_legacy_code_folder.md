# 002: Remove Legacy code Folder

## Goal

Remove the old `code/` directory now that the project runs from the packaged
`gz-terrain-gen` CLI.

## Changes Made

- Deleted the `code/` directory.
- Removed the obsolete `.gitignore` entry for `code/__pycache__/`.
- Updated README text so it no longer references legacy compatibility launchers.

## Verification

Commands run:

```bash
uv run gz-terrain-gen --help
uv run gz-terrain-gen split --help
uv run gz-terrain-gen mesh --help
uv run pytest
uv run python -m compileall -f src tests
test ! -d code
```

Result:

- CLI help loaded successfully.
- Tests passed: 4 passed.
- Source and tests compiled successfully.
- Confirmed `code/` no longer exists.

## Follow-Up Notes

- The CLI is now the only supported entrypoint.
- Old generated terrain samples were removed with `code/`.
- Regenerate terrain under `outputs/` when needed.
