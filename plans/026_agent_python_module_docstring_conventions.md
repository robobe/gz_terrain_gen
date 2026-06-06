# Add Module Description And Diagram Link Conventions

Status: executed

## Summary

Updated the agent rules so future Python modules include a brief top-level
description, and can link to relevant diagrams in `docs/` when that helps
explain the module's role.

## Key Changes

- Added `## Python Module Conventions` to `AGENTS.md`.
- Required short module docstrings for Python modules.
- Allowed relative references to stable documentation diagrams.
- Clarified placement around `from __future__ import ...`.
- Kept this change limited to agent rules.

## Verification

Planned checks:

```bash
test -f AGENTS.md
rg -n "Python Module Conventions|module docstring|docs/application_flow.md|docs/metadata_design.md|docs/architecture.md|from __future__" AGENTS.md
test -f plans/026_agent_python_module_docstring_conventions.md
git status --short
```
