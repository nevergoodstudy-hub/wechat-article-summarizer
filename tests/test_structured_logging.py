"""Tests for structured logging helpers."""

from __future__ import annotations

import builtins
import importlib

import pytest

from wechat_summarizer.shared.utils import structured_logging


@pytest.mark.unit
class TestStructuredLogging:
    """Tests for ``shared.utils.structured_logging``."""

    def test_loguru_sink_processor_formats_message(self, mocker) -> None:
        sink_logger = mocker.MagicMock()
        mocker.patch("loguru.logger.opt", return_value=sink_logger)

        message = structured_logging._loguru_sink_processor(
            logger=None,
            method_name="info",
            event_dict={
                "level": "INFO",
                "event": "article_fetched",
                "url": "https://example.com",
                "duration_ms": 123,
                "timestamp": "ignored",
            },
        )

        assert message == "article_fetched | url=https://example.com duration_ms=123"
        sink_logger.info.assert_called_once_with(message)

    def test_loguru_sink_processor_without_extra_fields(self, mocker) -> None:
        sink_logger = mocker.MagicMock()
        mocker.patch("loguru.logger.opt", return_value=sink_logger)

        message = structured_logging._loguru_sink_processor(
            logger=None,
            method_name="warning",
            event_dict={
                "level": "WARNING",
                "event": "article_skipped",
                "timestamp": "ignored",
            },
        )

        assert message == "article_skipped"
        sink_logger.warning.assert_called_once_with("article_skipped")

    def test_configure_structlog_and_bind_contextvars(self) -> None:
        structured_logging.configure_structlog(json_format=False, log_level="DEBUG")
        logger = structured_logging.get_struct_logger("test.module", request_id="req-1")

        logger.info("structured_log", step="text-mode")

        bound = structured_logging.bind_contextvars(trace_id="trace-1")
        assert isinstance(bound, dict)

        structured_logging.unbind_contextvars("trace_id")
        structured_logging.clear_contextvars()

    def test_reload_module_without_structlog_dependency(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mocker,
    ) -> None:
        original_import = builtins.__import__
        bind_mock = mocker.patch("loguru.logger.bind", return_value=object())

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
            if name == "structlog" or name.startswith("structlog."):
                raise ImportError("structlog missing")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        module = importlib.reload(structured_logging)

        try:
            assert module._structlog_available is False
            assert module.configure_structlog(json_format=False) is None
            logger = module.get_struct_logger("fallback.reload", request_id="req-3")
            assert logger is bind_mock.return_value
            assert module.bind_contextvars(trace_id="trace-3") == {}
        finally:
            monkeypatch.setattr(builtins, "__import__", original_import)
            importlib.reload(module)

    def test_configure_structlog_json_mode(self) -> None:
        structured_logging.configure_structlog(json_format=True, log_level="INFO")
        logger = structured_logging.get_struct_logger("json.logger")

        logger.info("structured_log", step="json-mode")

    def test_fallback_behaviour_when_structlog_is_unavailable(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mocker,
    ) -> None:
        sentinel = object()
        bind_mock = mocker.patch("loguru.logger.bind", return_value=sentinel)

        monkeypatch.setattr(structured_logging, "_structlog_available", False)
        monkeypatch.setattr(structured_logging, "structlog", None)

        logger = structured_logging.get_struct_logger("fallback.logger", request_id="req-2")

        assert logger is sentinel
        bind_mock.assert_called_once_with(module="fallback.logger", request_id="req-2")
        assert structured_logging.bind_contextvars(trace_id="trace-2") == {}

        structured_logging.unbind_contextvars("trace_id")
        structured_logging.clear_contextvars()
