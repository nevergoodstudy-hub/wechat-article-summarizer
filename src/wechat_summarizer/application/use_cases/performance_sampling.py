"""Lightweight performance sampling for application use cases."""

from __future__ import annotations

import time
import tracemalloc
from dataclasses import dataclass, field
from types import TracebackType
from typing import Literal


@dataclass(frozen=True)
class PerformanceSample:
    """Execution-time and memory sample for a use-case path."""

    name: str
    duration_ms: float
    peak_memory_kb: float
    metadata: dict[str, int | float | str | bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Return a serialization-friendly sample payload."""
        return {
            "name": self.name,
            "duration_ms": round(self.duration_ms, 2),
            "peak_memory_kb": round(self.peak_memory_kb, 1),
            "metadata": dict(self.metadata),
        }


class PerformanceSampler:
    """Context manager that samples elapsed time and Python allocation peak."""

    def __init__(
        self,
        name: str,
        metadata: dict[str, int | float | str | bool] | None = None,
    ) -> None:
        self._name = name
        self._metadata = metadata or {}
        self._start = 0.0
        self.sample = PerformanceSample(name=name, duration_ms=0.0, peak_memory_kb=0.0)
        self._started_tracemalloc = False

    def __enter__(self) -> PerformanceSampler:
        self._started_tracemalloc = not tracemalloc.is_tracing()
        if self._started_tracemalloc:
            tracemalloc.start()
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        duration_ms = (time.perf_counter() - self._start) * 1000
        _, peak = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, 0)
        if self._started_tracemalloc:
            tracemalloc.stop()

        self.sample = PerformanceSample(
            name=self._name,
            duration_ms=duration_ms,
            peak_memory_kb=peak / 1024,
            metadata=dict(self._metadata),
        )
        return False


__all__ = ["PerformanceSample", "PerformanceSampler"]
