# ADR-005: Add Performance Sampling and Cache Bounds

## Status
Accepted

## Context
Batch processing, GUI operations and caches can grow under repeated use. The project needs resource governance without turning the current application into a heavyweight observability platform.

## Decision
Add lightweight performance sampling for batch and GUI paths, and enforce bounded cache behavior with LRU, TTL and entry limits.

## Rationale
Sampling gives enough data for regression detection while keeping dependencies and runtime overhead low. Explicit cache limits prevent unbounded memory and disk growth.

## Trade-offs
The sampling model is less detailed than full distributed tracing. That is acceptable for a desktop and CLI application where local responsiveness and simplicity matter.

## Consequences
- Positive: Hot paths expose timing and allocation samples, and caches have predictable bounds.
- Negative: Samples are not a complete production telemetry system.
- Mitigation: Keep sampler APIs small so deeper telemetry can be added later without rewriting use cases.

