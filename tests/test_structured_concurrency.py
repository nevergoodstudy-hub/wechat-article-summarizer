"""Structured concurrency helper tests."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

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


@pytest.mark.unit
async def test_run_structured_tasks_flattens_exception_group_leaves() -> None:
    """Sibling failures should be exposed as leaf exceptions from ExceptionGroup."""

    started = asyncio.Event()

    async def fail_fast() -> None:
        raise ValueError("fast")

    async def fail_after_cancellation() -> None:
        started.set()
        try:
            await asyncio.sleep(1)
        finally:
            raise RuntimeError("cleanup")

    with pytest.raises(StructuredConcurrencyError) as exc_info:
        await run_structured_tasks([fail_after_cancellation(), fail_fast()])

    assert started.is_set()
    error_types = {type(error) for error in exc_info.value.errors}
    assert ValueError in error_types
    assert RuntimeError in error_types


@pytest.mark.unit
def test_structured_concurrency_uses_except_star() -> None:
    """P1-2 requires native except* handling for TaskGroup ExceptionGroup."""
    source_path = (
        Path(__file__).parents[1]
        / "src"
        / "wechat_summarizer"
        / "shared"
        / "utils"
        / "structured_concurrency.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))

    assert any(isinstance(node, ast.TryStar) for node in ast.walk(tree))
