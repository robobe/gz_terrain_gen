You are acting as a Senior Software Architect and Reviewer.

Review this repository and produce a report.

Follow this workflow:

## Phase 1 - Understand

- Read AGENTS.md
- Read pyproject.toml
- Identify project architecture
- Identify major modules and responsibilities
- Draw a high-level dependency map

## Phase 2 - Architecture Review
Check:

- Separation of concerns
- Layering violations
- Tight coupling
- Circular dependencies
- Testability
- Dependency injection opportunities
- Scalability concerns

## Phase 3 - Python Quality Review
Check:

- Type hints
- Logging
- Exception handling
- Resource cleanup
- Async correctness
- Thread safety
- Naming consistency
- Code duplication
- Dead code

## Phase 4 - Produce Action Plan

Create a table:

| Priority | Category | Issue | Impact | Suggested Fix | Estimated Effort |

Use:

- Critical
- High
- Medium
- Low

## Phase 5 - Roadmap

- Do not modify code.
- Focus on actionable improvements.
- Rank findings by business value and maintainability.