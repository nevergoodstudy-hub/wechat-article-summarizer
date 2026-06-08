"""Structured concurrency helpers with Python 3.10 compatibility."""

from __future__ import annotations

import asyncio
import builtins
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
    """Flatten native ExceptionGroup/BaseExceptionGroup without 3.11-only syntax."""
    group_type = getattr(builtins, "BaseExceptionGroup", None)
    if group_type is not None and isinstance(error, group_type):
        flattened: list[BaseException] = []
        for nested in getattr(error, "exceptions", ()):
            flattened.extend(_flatten_exception_group(nested))
        return flattened
    return [error]


async def run_structured_tasks(
    coroutines: Iterable[Coroutine[Any, Any, T]],
) -> list[T]:
    """Run child tasks with TaskGroup semantics and ordered results.

    Python 3.11+ uses native ``asyncio.TaskGroup``. Python 3.10 falls back to
    a small compatibility runner that cancels pending siblings on first error.
    """
    coroutine_list = list(coroutines)
    if not coroutine_list:
        return []

    if hasattr(asyncio, "TaskGroup"):
        tasks: list[asyncio.Task[T]] = []
        try:
            async with asyncio.TaskGroup() as task_group:
                tasks = [task_group.create_task(coroutine) for coroutine in coroutine_list]
        except Exception as exc:
            raise StructuredConcurrencyError(_flatten_exception_group(exc)) from exc
        return [task.result() for task in tasks]

    return await _run_structured_tasks_compat(coroutine_list)


async def _run_structured_tasks_compat(
    coroutines: list[Coroutine[Any, Any, T]],
) -> list[T]:
    """Python 3.10-compatible TaskGroup subset."""
    tasks = [asyncio.create_task(coroutine) for coroutine in coroutines]

    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        errors: list[BaseException] = []

        for task in done:
            if task.cancelled():
                continue
            error = task.exception()
            if error is not None:
                errors.append(error)

        if errors:
            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            raise StructuredConcurrencyError(errors)

        if pending:
            await asyncio.gather(*pending)

        return [task.result() for task in tasks]
    except BaseException:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise


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
