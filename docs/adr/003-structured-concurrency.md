# ADR-003: Use TaskGroup for Batch Concurrency

## Status
Accepted

## Context
Batch processing needs predictable cancellation, bounded concurrency and observable error handling. Older gather-based flows can hide related failures or leave task lifecycle behavior implicit.

## Decision
Use Python 3.11+ `asyncio.TaskGroup`, semaphores and `except*` handling for async batch processing.

## Rationale
TaskGroup makes structured concurrency explicit in the standard library. It fits the project's Python 3.11+ baseline and keeps concurrent batch behavior easier to test.

## Trade-offs
The runtime baseline is higher than Python 3.10. This is acceptable because the project already targets modern Python and CI covers supported versions.

## Consequences
- Positive: Batch task lifecycle, concurrency limits and grouped failures are easier to reason about.
- Negative: Downstream users on Python 3.10 must upgrade.
- Mitigation: Document the Python baseline and keep CI matrix coverage across current supported versions.

