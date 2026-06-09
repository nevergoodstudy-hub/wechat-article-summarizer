# ADR-001: Enforce Clean Architecture Boundaries

## Status
Accepted

## Context
The project follows DDD and hexagonal architecture. Domain code must remain independent of infrastructure, presentation and MCP runtime details, but this rule is hard to preserve during a broad refactor without automated checks.

## Decision
Keep domain and application boundaries explicit, and enforce them with repository scripts and CI quality gates. Infrastructure continues to implement outbound ports, while domain code remains free of outer-layer imports.

## Rationale
Automated guards make the architectural rule executable, not just documentary. They also reduce review burden because accidental imports are caught before merge.

## Trade-offs
The guard can reject a legitimate change until the boundary rule is expressed through a protocol or adapter. That extra design step is acceptable because it keeps the long-term dependency direction stable.

## Consequences
- Positive: Boundary regressions become visible in local and CI runs.
- Negative: Some changes need small port abstractions before implementation can proceed.
- Mitigation: Keep guard messages specific and add tests for accepted import patterns.

