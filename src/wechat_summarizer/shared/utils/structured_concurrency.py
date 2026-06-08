"""Structured concurrency helpers backed by native Python 3.11 TaskGroup."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Iterable
from typing import Any, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class StructuredConcurrencyError(Exception):
    """Raised when one or more structured child tasks fail."""

    def __init__(self, errors: Iterable[BaseException]) -> None:
        self.errors = tuple(errors)
        details = ", ".join(f"{type(error).__name__}: {error}" for error in self.errors)
        super().__init__(details or "structured concurrency task failed")


def _flatten_exception_group(error: BaseException) -> list[BaseException]:
    """Flatten native ExceptionGroup/BaseExceptionGroup into leaf exceptions."""
    if isinstance(error, BaseExceptionGroup):
        flattened: list[BaseException] = []
        for nested in error.exceptions:
            flattened.extend(_flatten_exception_group(nested))
        return flattened
    return [error]


async def run_structured_tasks(
    coroutines: Iterable[Coroutine[Any, Any, T]],
) -> list[T]:
    """Run child tasks with TaskGroup semantics and ordered results.

    Native ``asyncio.TaskGroup`` cancels pending siblings on first failure and
    raises an ``ExceptionGroup``. ``except*`` keeps that path explicit while the
    public helper still exposes a stable ``StructuredConcurrencyError``.
    """
    coroutine_list = list(coroutines)
    if not coroutine_list:
        return []

    tasks: list[asyncio.Task[T]] = []
    try:
        async with asyncio.TaskGroup() as task_group:
            tasks = [task_group.create_task(coroutine) for coroutine in coroutine_list]
    except* Exception as exc_group:
        raise StructuredConcurrencyError(_flatten_exception_group(exc_group)) from exc_group
    return [task.result() for task in tasks]


async def run_limited_tasks(
    items: Iterable[T],
    limit: int,
    worker: Callable[[T], Coroutine[Any, Any, R]],
) -> list[R]:
    """Run a worker over items with structured tasks and concurrency limiting."""
    if limit < 1:
        raise ValueError("并发数必须大于 0")

    semaphore = asyncio.Semaphore(limit)

    async def run_one(item: T) -> R:
        async with semaphore:
            return await worker(item)

    return await run_structured_tasks(run_one(item) for item in items)
