"""Tests for MCP toolset response contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from wechat_summarizer.mcp.resources.article_content import register_article_resources
from wechat_summarizer.mcp.responses import BUSINESS_ERROR_CODE, VALIDATION_ERROR_CODE
from wechat_summarizer.mcp.security import SecurityManager, reset_security_manager
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


@pytest.fixture(autouse=True)
def _disable_mcp_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep toolset contract tests focused on tool responses, not global rate buckets."""
    reset_security_manager()
    manager = SecurityManager(enable_audit=False, enable_rate_limit=False)
    monkeypatch.setattr(
        "wechat_summarizer.mcp.security.get_security_manager",
        lambda: manager,
    )
    yield
    reset_security_manager()


class _FailingArticleWorkflow:
    def fetch(self, url: str) -> object:
        raise RuntimeError("api_key=sk-secret-token fetch failed")

    def summarize(self, url: str, method: str, max_length: int) -> object:
        raise RuntimeError("summary failed")

    def get_info(self, url: str) -> object:
        raise RuntimeError("info failed")

    def batch_summarize(self, urls: list[str], method: str, max_length: int) -> object:
        raise RuntimeError("batch failed")

    def list_available_methods(self) -> list[str]:
        return ["simple"]


class _FailingAnalysisWorkflow:
    def graph_analyze(self, url: str) -> object:
        raise RuntimeError("graph failed")

    def compare_articles(self, urls: list[str], aspects: list[str]) -> object:
        raise RuntimeError("compare failed")

    def track_topic(self, urls: list[str], topic: str) -> object:
        raise RuntimeError("topic failed")

    def evaluate_summary(self, url: str, summary_text: str | None, method: str) -> object:
        raise RuntimeError("evaluate failed")


@pytest.mark.unit
async def test_article_tools_return_standard_validation_error() -> None:
    """Article tools should expose the shared MCP validation error contract."""
    mcp = _CapturingMCP()
    register_article_tools(mcp, lambda: object())  # type: ignore[arg-type]

    result = await mcp.tools["fetch_article"]("ftp://example.com/article")

    assert result["success"] is False
    assert result["isError"] is True
    assert result["error_code"] == VALIDATION_ERROR_CODE
    assert result["error_type"] == "validation"
    assert "参数校验失败" in result["error"]


@pytest.mark.unit
async def test_article_tools_use_configured_url_and_summary_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Article tools should consume MCP security limits."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_batch_urls", 1)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_summary_length", 80)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["example.com"])
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
async def test_article_tools_return_standard_business_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Article workflow failures should use the shared business error contract."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["example.com"])
    mcp = _CapturingMCP()
    register_article_tools(mcp, lambda: _FailingArticleWorkflow())  # type: ignore[arg-type]

    result = await mcp.tools["fetch_article"]("https://example.com/a")
    batch_result = await mcp.tools["batch_summarize"](["https://example.com/a"])

    assert result["success"] is False
    assert result["isError"] is True
    assert result["error_code"] == BUSINESS_ERROR_CODE
    assert result["error_type"] == "business"
    assert "api_key=***REDACTED***" in result["error"]
    assert "sk-secret-token" not in result["error"]
    assert batch_result["error_code"] == BUSINESS_ERROR_CODE
    assert batch_result["error_type"] == "business"


@pytest.mark.unit
async def test_analysis_tools_return_standard_validation_error() -> None:
    """Analysis tools should use the same validation error shape."""
    mcp = _CapturingMCP()
    register_analysis_tools(mcp, lambda: object())  # type: ignore[arg-type]

    result = await mcp.tools["get_audit_logs"](limit=0)

    assert result["success"] is False
    assert result["isError"] is True
    assert result["error_code"] == VALIDATION_ERROR_CODE
    assert result["error_type"] == "validation"
    assert "limit must be in [1, 100]" in result["error"]


@pytest.mark.unit
async def test_analysis_tools_use_configured_text_and_audit_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Analysis tools should consume MCP security limits instead of literals."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_topic_length", 3)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_text_length", 5)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "max_audit_logs", 2)
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["example.com"])
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
async def test_analysis_tools_return_standard_business_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Analysis workflow failures should be distinguishable from validation errors."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["example.com"])
    mcp = _CapturingMCP()
    register_analysis_tools(mcp, lambda: _FailingAnalysisWorkflow())  # type: ignore[arg-type]

    result = await mcp.tools["graph_analyze"]("https://example.com/a")

    assert result["success"] is False
    assert result["isError"] is True
    assert result["error_code"] == BUSINESS_ERROR_CODE
    assert result["error_type"] == "business"
    assert result["error"] == "graph failed"


@pytest.mark.unit
async def test_analysis_tools_return_business_error_for_business_rules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Local MCP business rules should not be reported as validation failures."""
    monkeypatch.setitem(MCP_SECURITY_CONFIG, "allowed_network_hosts", ["example.com"])
    mcp = _CapturingMCP()
    register_analysis_tools(mcp, lambda: _FailingAnalysisWorkflow())  # type: ignore[arg-type]

    result = await mcp.tools["compare_articles"](["https://example.com/a"])
    audit_result = await mcp.tools["get_audit_logs"]()

    assert result["success"] is False
    assert result["error_code"] == BUSINESS_ERROR_CODE
    assert result["error_type"] == "business"
    assert "至少需要 2 篇文章" in result["error"]
    assert audit_result["error_code"] == BUSINESS_ERROR_CODE
    assert audit_result["error_type"] == "business"
    assert "审计日志未启用" in audit_result["error"]


@pytest.mark.unit
async def test_article_resource_returns_standard_validation_text() -> None:
    """Resources should share the same human-readable validation wording."""
    mcp = _CapturingMCP()
    register_article_resources(mcp, lambda: object())  # type: ignore[arg-type]

    result = await mcp.resources["article://{url}"]("file:///etc/passwd")

    assert result.startswith("参数校验失败:")
    assert "Disallowed URL scheme" in result
