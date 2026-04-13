"""Article-related MCP resources."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from ...features.article_workflow import ArticleWorkflowService
from ..input_validator import MCPInputValidator

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


ArticleWorkflowFactory = Callable[[], ArticleWorkflowService]


def _default_service_factory() -> ArticleWorkflowService:
    from ...infrastructure.config import get_container

    return get_container().article_workflow_service


def register_article_resources(
    mcp_instance: FastMCP,
    service_factory: ArticleWorkflowFactory | None = None,
) -> None:
    """Register article content resources on an MCP server."""
    get_service = service_factory or _default_service_factory

    @mcp_instance.resource("article://{url}")
    async def get_article_content(url: str) -> str:
        """Expose fetched article content as a resource."""
        try:
            url = MCPInputValidator.validate_url(url)
            payload = await asyncio.to_thread(get_service().fetch, url, None)
            return f"""# {payload.title}

**作者**: {payload.author or "未知"}
**来源**: {payload.account_name or "未知"}
**发布时间**: {payload.publish_time}
**字数**: {payload.word_count}

---

{payload.content}
"""
        except Exception as exc:
            return f"获取文章失败: {exc}"
