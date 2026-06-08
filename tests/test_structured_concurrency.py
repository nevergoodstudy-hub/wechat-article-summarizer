"""Structured concurrency helper tests."""

from __future__ import annotations

import asyncio

import pytest

from wechat_summarizer.shared.utils.structured_concurrency import (
    StructuredConcurrencyError,
    run_limited_tasks,
    run_structured_tasks,
)


@pytest.mark.unit
async def test_run_structured_tasks_preserves_input_order() -> None:
    """Results are returned in input order, even when tasks finish out of order."""

    async def worker(value: int) -> int:
        await asyncio.sleep(0.01 if value == 1 else 0.0)
        return value

    result = await run_structured_tasks(worker(value) for value in [1, 2, 3])

    assert result == [1, 2, 3]


@pytest.mark.unit
async def test_run_limited_tasks_enforces_concurrency_limit() -> None:
    """Semaphore limiting should cap concurrent child tasks."""
    running = 0
    max_seen = 0
    lock = asyncio.Lock()

    async def worker(value: int) -> int:
        nonlocal running, max_seen
        async with lock:
            running += 1
            max_seen = max(max_seen, running)
        await asyncio.sleep(0.01)
        async with lock:
            running -= 1
        return value

    result = await run_limited_tasks(range(6), 2, worker)

    assert result == [0, 1, 2, 3, 4, 5]
    assert max_seen <= 2


@pytest.mark.unit
async def test_run_structured_tasks_wraps_exception_groups() -> None:
    """Native TaskGroup ExceptionGroup errors should be exposed in a stable wrapper."""

    async def fail() -> None:
        raise ValueError("boom")

    async def wait() -> None:
        await asyncio.sleep(0.1)

    with pytest.raises(StructuredConcurrencyError) as exc_info:
        await run_structured_tasks([fail(), wait()])

    assert any(isinstance(error, ValueError) for error in exc_info.value.errors)
