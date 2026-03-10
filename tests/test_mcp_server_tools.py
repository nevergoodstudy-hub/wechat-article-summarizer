"""MCP server 工具与资源入口的集成级回归测试。"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

import pytest

from wechat_summarizer.mcp import server
from wechat_summarizer.mcp.security import SecurityManager, reset_security_manager


class DummyMCP:
    """收集注册后的 MCP 工具与资源。"""

    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}
        self.resources: dict[str, Any] = {}

    def tool(self):  # type: ignore[no-untyped-def]
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def resource(self, uri_template: str):  # type: ignore[no-untyped-def]
        def decorator(func):
            self.resources[uri_template] = func
            return func

        return decorator


@pytest.fixture(autouse=True)
def _reset_security_manager() -> Any:
    reset_security_manager()
    yield
    reset_security_manager()


def _security_manager() -> SecurityManager:
    return SecurityManager(enable_audit=False, enable_rate_limit=False)


def _register_tools() -> dict[str, Any]:
    mcp = DummyMCP()
    server._register_tools(mcp)
    return mcp.tools


def _register_resources() -> dict[str, Any]:
    mcp = DummyMCP()
    server._register_resources(mcp)
    return mcp.resources


def _make_article(url: str = "https://mp.weixin.qq.com/s/default") -> Any:
    return SimpleNamespace(
        title=f"文章 {url.rsplit('/', maxsplit=1)[-1]}",
        author="作者",
        account_name="公众号",
        publish_time_str="2026-03-10",
        word_count=128,
        content_text="人工智能发展迅速，人工智能应用广泛，模型能力持续提升。",
        attach_summary=Mock(),
    )


def _make_summary(content: str = "这是摘要") -> Any:
    return SimpleNamespace(
        content=content,
        key_points=["要点 1"],
        tags=["AI"],
        method=SimpleNamespace(value="simple"),
        model_name="test-model",
    )


def test_summarize_article_uses_mcp_validation_helpers() -> None:
    tools = _register_tools()
    article = _make_article()
    summary = _make_summary()
    fetch_execute = Mock(return_value=article)
    summarize_execute = Mock(return_value=summary)
    container = SimpleNamespace(
        fetch_use_case=SimpleNamespace(execute=fetch_execute),
        summarize_use_case=SimpleNamespace(execute=summarize_execute),
    )

    with (
        patch(
            "wechat_summarizer.mcp.security.get_security_manager",
            return_value=_security_manager(),
        ),
        patch(
            "wechat_summarizer.mcp.server._validate_mcp_url",
            return_value="https://mp.weixin.qq.com/s/validated",
        ) as mock_validate_url,
        patch(
            "wechat_summarizer.mcp.server.MCPInputValidator.validate_method",
            return_value="simple",
        ) as mock_validate_method,
        patch(
            "wechat_summarizer.mcp.server._validate_summary_length",
            return_value=321,
        ) as mock_validate_length,
        patch(
            "wechat_summarizer.mcp.server.get_container",
            return_value=container,
        ),
    ):
        result = asyncio.run(
            tools["summarize_article"](
                url="https://example.com/raw",
                method=" SIMPLE ",
                max_length=999,
            )
        )

    assert result["success"] is True
    mock_validate_url.assert_called_once_with("https://example.com/raw")
    mock_validate_method.assert_called_once_with(" SIMPLE ")
    mock_validate_length.assert_called_once_with(999)
    assert fetch_execute.call_args.args == ("https://mp.weixin.qq.com/s/validated",)
    assert summarize_execute.call_args.kwargs == {"method": "simple", "max_length": 321}
    article.attach_summary.assert_called_once_with(summary)


def test_get_article_info_uses_mcp_url_validator() -> None:
    tools = _register_tools()
    article = _make_article()
    fetch_execute = Mock(return_value=article)
    container = SimpleNamespace(fetch_use_case=SimpleNamespace(execute=fetch_execute))

    with (
        patch(
            "wechat_summarizer.mcp.security.get_security_manager",
            return_value=_security_manager(),
        ),
        patch(
            "wechat_summarizer.mcp.server._validate_mcp_url",
            return_value="https://mp.weixin.qq.com/s/info",
        ) as mock_validate_url,
        patch(
            "wechat_summarizer.mcp.server.get_container",
            return_value=container,
        ),
    ):
        result = asyncio.run(tools["get_article_info"](url="https://example.com/info"))

    assert result["success"] is True
    assert result["title"] == article.title
    mock_validate_url.assert_called_once_with("https://example.com/info")
    assert fetch_execute.call_args.args == ("https://mp.weixin.qq.com/s/info",)


def test_graph_analyze_uses_mcp_url_validator() -> None:
    tools = _register_tools()
    article = _make_article()
    fetch_execute = Mock(return_value=article)
    knowledge_graph = SimpleNamespace(
        entity_count=0,
        relationship_count=0,
        community_count=0,
        entities={},
        relationships={},
        communities={},
        get_entity=Mock(return_value=None),
    )
    graphrag_summarizer = SimpleNamespace(
        summarize=Mock(return_value=None),
        get_knowledge_graph=Mock(return_value=knowledge_graph),
    )
    container = SimpleNamespace(
        fetch_use_case=SimpleNamespace(execute=fetch_execute),
        summarizers={"graphrag-openai": graphrag_summarizer},
    )

    with (
        patch(
            "wechat_summarizer.mcp.security.get_security_manager",
            return_value=_security_manager(),
        ),
        patch(
            "wechat_summarizer.mcp.server._validate_mcp_url",
            return_value="https://mp.weixin.qq.com/s/graph",
        ) as mock_validate_url,
        patch(
            "wechat_summarizer.mcp.server.get_container",
            return_value=container,
        ),
    ):
        result = asyncio.run(tools["graph_analyze"](url="https://example.com/graph"))

    assert result["success"] is True
    mock_validate_url.assert_called_once_with("https://example.com/graph")
    assert fetch_execute.call_args.args == ("https://mp.weixin.qq.com/s/graph",)
    graphrag_summarizer.summarize.assert_called_once()
    graphrag_summarizer.get_knowledge_graph.assert_called_once_with()


def test_evaluate_summary_sanitizes_user_supplied_text() -> None:
    tools = _register_tools()
    article = _make_article()
    fetch_execute = Mock(return_value=article)
    summarize_execute = Mock(side_effect=AssertionError("should not generate summary"))
    container = SimpleNamespace(
        fetch_use_case=SimpleNamespace(execute=fetch_execute),
        summarize_use_case=SimpleNamespace(execute=summarize_execute),
    )

    with (
        patch(
            "wechat_summarizer.mcp.security.get_security_manager",
            return_value=_security_manager(),
        ),
        patch(
            "wechat_summarizer.mcp.server._validate_mcp_url",
            return_value="https://mp.weixin.qq.com/s/evaluate",
        ) as mock_validate_url,
        patch(
            "wechat_summarizer.mcp.server.MCPInputValidator.validate_method",
            return_value="simple",
        ) as mock_validate_method,
        patch(
            "wechat_summarizer.mcp.server._sanitize_mcp_text",
            return_value="人工智能应用总结",
        ) as mock_sanitize_text,
        patch(
            "wechat_summarizer.mcp.server.get_container",
            return_value=container,
        ),
    ):
        result = asyncio.run(
            tools["evaluate_summary"](
                url="https://example.com/evaluate",
                summary_text="原始摘要",
                method=" SIMPLE ",
            )
        )

    assert result["success"] is True
    assert result["summary"] == "人工智能应用总结"
    mock_validate_url.assert_called_once_with("https://example.com/evaluate")
    mock_validate_method.assert_called_once_with(" SIMPLE ")
    mock_sanitize_text.assert_called_once_with(
        "原始摘要",
        max_length_key="max_summary_length",
    )
    summarize_execute.assert_not_called()


def test_batch_summarize_processes_all_validated_urls() -> None:
    tools = _register_tools()
    urls = [f"https://mp.weixin.qq.com/s/{index}" for index in range(11)]
    fetch_execute = Mock(side_effect=lambda url: _make_article(url))
    summarize_execute = Mock(
        side_effect=lambda article, method, max_length: _make_summary(
            content=f"{article.title}-{method}-{max_length}"
        )
    )
    container = SimpleNamespace(
        fetch_use_case=SimpleNamespace(execute=fetch_execute),
        summarize_use_case=SimpleNamespace(execute=summarize_execute),
    )

    with (
        patch(
            "wechat_summarizer.mcp.security.get_security_manager",
            return_value=_security_manager(),
        ),
        patch(
            "wechat_summarizer.mcp.server._validate_mcp_urls",
            return_value=urls,
        ) as mock_validate_urls,
        patch(
            "wechat_summarizer.mcp.server.MCPInputValidator.validate_method",
            return_value="simple",
        ),
        patch(
            "wechat_summarizer.mcp.server._validate_summary_length",
            return_value=256,
        ),
        patch(
            "wechat_summarizer.mcp.server.get_container",
            return_value=container,
        ),
    ):
        result = asyncio.run(
            tools["batch_summarize"](
                urls=["placeholder"],
                method="simple",
                max_length=256,
            )
        )

    mock_validate_urls.assert_called_once_with(["placeholder"])
    assert result["total"] == len(urls)
    assert result["processed"] == len(urls)
    assert fetch_execute.call_count == len(urls)
    assert summarize_execute.call_count == len(urls)


def test_article_resource_validates_url_and_formats_markdown() -> None:
    resources = _register_resources()
    article = _make_article("https://mp.weixin.qq.com/s/resource")
    fetch_execute = Mock(return_value=article)
    container = SimpleNamespace(fetch_use_case=SimpleNamespace(execute=fetch_execute))

    with (
        patch(
            "wechat_summarizer.mcp.server._validate_mcp_url",
            return_value="https://mp.weixin.qq.com/s/resource",
        ) as mock_validate_url,
        patch(
            "wechat_summarizer.mcp.server.get_container",
            return_value=container,
        ),
    ):
        result = asyncio.run(resources["article://{url}"](url="https://example.com/resource"))

    mock_validate_url.assert_called_once_with("https://example.com/resource")
    assert fetch_execute.call_args.args == ("https://mp.weixin.qq.com/s/resource",)
    assert article.title in result
    assert article.content_text in result
