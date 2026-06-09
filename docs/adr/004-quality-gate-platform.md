# ADR-004: Use a Unified Quality Gate

## Status
Accepted

## Context
The refactor spans architecture boundaries, security checks, typing, linting, tests and CI workflow policy. Running these checks manually in different combinations makes completion evidence inconsistent.

## Decision
Use `scripts/quality_gate.py` as the local and CI entry point for lint, architecture, mypy, tests and security smoke checks. Add focused guard scripts for architectural invariants that normal tests do not prove.

## Rationale
A unified gate gives each checklist item an executable proof path. Focused scripts keep broad rules such as CI matrix coverage and pytest marker policy from becoming tribal knowledge.

## Trade-offs
Quality gates add maintenance cost and can slow local iteration. The cost is acceptable because the project is security-sensitive and the refactor requires traceable evidence.

## Consequences
- Positive: Local validation and CI validation use the same vocabulary.
- Negative: Guard scripts can become stale if workflows change.
- Mitigation: Add unit tests for each guard script and keep failure messages actionable.

