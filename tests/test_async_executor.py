"""Tests for the shared async executor."""

from __future__ import annotations

import asyncio
import threading

import pytest

from wechat_summarizer.infrastructure.async_executor import (
    AsyncTaskExecutor,
    GUIAsyncHelper,
    get_async_executor,
    run_async,
    submit_async,
)


@pytest.fixture(autouse=True)
def reset_async_executor() -> None:
    """Reset singleton state between tests."""
    AsyncTaskExecutor.reset()
    yield
    AsyncTaskExecutor.reset()


async def _add(a: int, b: int) -> int:
    await asyncio.sleep(0.01)
    return a + b


async def _fail() -> int:
    await asyncio.sleep(0.01)
    raise ValueError("boom")


@pytest.mark.unit
class TestAsyncTaskExecutor:
    """Tests for ``AsyncTaskExecutor``."""

    def test_singleton_and_run_sync_helpers(self) -> None:
        first = get_async_executor()
        second = get_async_executor()

        assert first is second
        assert first.is_running is True
        assert run_async(_add(1, 2), timeout=2) == 3

    def test_submit_returns_future_result(self) -> None:
        future = submit_async(_add(2, 3))

        assert future.result(timeout=2) == 5

    def test_run_with_callback_invokes_success_callback(self) -> None:
        executor = get_async_executor()
        results: list[int] = []
        callback_called = threading.Event()

        future = executor.run_with_callback(
            _add(4, 5),
            on_success=lambda value: (results.append(value), callback_called.set()),
            ui_callback=lambda delay, callback: callback(),
        )

        assert future.result(timeout=2) == 9
        assert callback_called.wait(1) is True
        assert results == [9]

    def test_run_with_callback_invokes_error_callback(self) -> None:
        executor = get_async_executor()
        errors: list[str] = []
        callback_called = threading.Event()

        future = executor.run_with_callback(
            _fail(),
            on_error=lambda error: (errors.append(str(error)), callback_called.set()),
            ui_callback=lambda delay, callback: callback(),
        )

        with pytest.raises(ValueError, match="boom"):
            future.result(timeout=2)

        assert callback_called.wait(1) is True
        assert errors == ["boom"]

    def test_shutdown_prevents_new_tasks(self) -> None:
        executor = get_async_executor()
        executor.shutdown(wait=True)

        coro = _add(1, 1)
        try:
            with pytest.raises(RuntimeError):
                executor.submit(coro)
        finally:
            coro.close()

    def test_reset_creates_new_instance(self) -> None:
        first = get_async_executor()

        AsyncTaskExecutor.reset()

        second = get_async_executor()
        assert first is not second


@pytest.mark.unit
class TestGUIAsyncHelper:
    """Tests for ``GUIAsyncHelper``."""

    def test_helper_runs_async_callbacks_in_ui_context(self) -> None:
        ui_calls: list[object] = []
        results: list[int] = []
        callback_called = threading.Event()

        def ui_callback(delay: int, callback) -> None:  # type: ignore[no-untyped-def]
            ui_calls.append(delay)
            callback()

        helper = GUIAsyncHelper(ui_callback)
        future = helper.run(
            _add(10, 5),
            on_success=lambda value: (results.append(value), callback_called.set()),
        )

        assert future.result(timeout=2) == 15
        assert callback_called.wait(1) is True
        assert results == [15]
        assert ui_calls[0] == 0

        helper.run_in_ui(lambda: ui_calls.append("manual"), delay_ms=25)
        assert 25 in ui_calls
        assert "manual" in ui_calls
