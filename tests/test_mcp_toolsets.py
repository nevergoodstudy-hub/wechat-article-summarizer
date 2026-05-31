"""Tests for MCP toolset response contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from wechat_summarizer.mcp.resources.article_content import register_article_resources
from wechat_summarizer.mcp.responses import VALIDATION_ERROR_CODE
from wechat_summarizer.mcp.security_config import MCP_SECURITY_CONFIG
from wechat_summarizer.mcp.toolsets.analysis_tools import register_analysis_tools
from wechat_summarizer.mcp.toolsets.article_tools import register_article_tools


class _CapturingMCP:
    """Minimal MCP double that stores decorated tools and resources."""

    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., Any]] = {}
        self.resources: dict[str, Callable[..., Any]] = {}

    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.tools[func.__name__] = func
            return func

        return decorator

    def resource(self, uri: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.resources[uri] = func
            return func

        return decorator


@pytest.mark.unit
async def test_article_tools_return_standard_validation_error() -> None:
    """Article tools should expose the shared MCP validation error contract."""
    mcp = _CapturingMCP()
    register_article_tools(mcp, lambda: object())  # type: ignore[arg-type]

    result = await mcp.tools["fetch_article"]("ftp://example.com/article")

    assert result["success"] is False
    assert result["error_code"] == VALIDATION_ERROR_CODE
    assert "参数校验失败" in result["error"]


@pytest.mark.unit
async def test_article_tools_use_configured_url_and_summary_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Article tools should consume MCP security limits."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_batch_urls", 1)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_summary_length", 80)
    mcp = _CapturingMCP()
    register_article_tools(mcp, lambda: object())  # type: ignore[arg-type]

    too_many = await mcp.tools["batch_summarize"](
        ["https://example.com/a", "https://example.com/b"]
    )
    too_long = await mcp.tools["summarize_article"](
        "https://example.com/a",
        max_length=81,
    )

    assert too_many["error_code"] == VALIDATION_ERROR_CODE
    assert "Too many URLs: 2 > 1" in too_many["error"]
    assert too_long["error_code"] == VALIDATION_ERROR_CODE
    assert "max_length must be integer in [50, 80]" in too_long["error"]


@pytest.mark.unit
async def test_analysis_tools_return_standard_validation_error() -> None:
    """Analysis tools should use the same validation error shape."""
    mcp = _CapturingMCP()
    register_analysis_tools(mcp, lambda: object())  # type: ignore[arg-type]

    result = await mcp.tools["get_audit_logs"](limit=0)

    assert result["success"] is False
    assert result["error_code"] == VALIDATION_ERROR_CODE
    assert "limit must be in [1, 100]" in result["error"]


@pytest.mark.unit
async def test_analysis_tools_use_configured_text_and_audit_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Analysis tools should consume MCP security limits instead of literals."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_topic_length", 3)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_text_length", 5)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_audit_logs", 2)
    mcp = _CapturingMCP()
    register_analysis_tools(mcp, lambda: object())  # type: ignore[arg-type]

    topic_result = await mcp.tools["track_topic"](["https://example.com/a"], "abcd")
    summary_result = await mcp.tools["evaluate_summary"](
        "https://example.com/a",
        summary_text="abcdef",
    )
    audit_result = await mcp.tools["get_audit_logs"](limit=3)

    assert topic_result["error_code"] == VALIDATION_ERROR_CODE
    assert "Input too long: 4 > 3" in topic_result["error"]
    assert summary_result["error_code"] == VALIDATION_ERROR_CODE
    assert "Input too long: 6 > 5" in summary_result["error"]
    assert audit_result["error_code"] == VALIDATION_ERROR_CODE
    assert "limit must be in [1, 2]" in audit_result["error"]


@pytest.mark.unit
async def test_article_resource_returns_standard_validation_text() -> None:
    """Resources should share the same human-readable validation wording."""
    mcp = _CapturingMCP()
    register_article_resources(mcp, lambda: object())  # type: ignore[arg-type]

    result = await mcp.resources["article://{url}"]("file:///etc/passwd")

    assert result.startswith("参数校验失败:")
    assert "Disallowed URL scheme" in result
