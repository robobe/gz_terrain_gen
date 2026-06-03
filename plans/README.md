# Plan Records

All plans for this project must be saved in this folder, including proposed
plans that are not executed.

## Rule

Whenever Codex creates or receives a plan, save it under `plans/` as a numbered
Markdown file. If the plan is later executed, update the same file with the
execution result instead of creating a duplicate.

## Status Values

- `proposed`: plan was created but not executed yet.
- `executed`: plan was implemented and verified.
- `skipped`: plan was intentionally not used.
- `superseded`: plan was replaced by a newer plan.

## File Naming

Use the next available number and a short snake_case description:

```text
001_short_description.md
002_short_description.md
003_initialize_git_tracking.md
```

## Required Sections

Each plan file should include:

- Status
- Date
- Goal
- Planned Changes
- Verification Plan
- Execution Result
- Follow-Up Notes

For proposed plans, leave `Execution Result` as `Not executed yet`.
