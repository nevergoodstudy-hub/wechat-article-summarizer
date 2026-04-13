"""Article workflow MCP toolset."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from loguru import logger

from ...features.article_workflow import ArticleWorkflowService
from ..input_validator import MCPInputValidator, MCPValidationError
from ..security import PermissionLevel, require_permission

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


ArticleWorkflowFactory = Callable[[], ArticleWorkflowService]

_METHOD_DESCRIPTIONS = {
    "simple": "基于规则的简单摘要，无需 AI",
    "textrank": "基于 TextRank 算法的抽取式摘要",
    "ollama": "使用本地 Ollama 模型",
    "openai": "使用 OpenAI GPT 模型",
    "anthropic": "使用 Anthropic Claude 模型",
    "zhipu": "使用智谱 GLM 模型",
    "deepseek": "使用 DeepSeek 模型",
    "rag-*": "RAG 增强摘要（基于向量检索）",
    "graphrag-*": "GraphRAG 摘要（基于知识图谱）",
}


def _default_service_factory() -> ArticleWorkflowService:
    from ...infrastructure.config import get_container

    return get_container().article_workflow_service


def register_article_tools(
    mcp_instance: FastMCP,
    service_factory: ArticleWorkflowFactory | None = None,
) -> None:
    """Register article workflow tools on an MCP server."""
    get_service = service_factory or _default_service_factory

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def fetch_article(url: str) -> dict[str, object]:
        """Fetch a supported article."""
        try:
            url = MCPInputValidator.validate_url(url)
            payload = await asyncio.to_thread(get_service().fetch, url)
            return {
                "success": True,
                "title": payload.title,
                "author": payload.author,
                "account_name": payload.account_name,
                "publish_time": payload.publish_time,
                "word_count": payload.word_count,
                "content": payload.content,
                "content_truncated": payload.content_truncated,
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
        except Exception as exc:
            logger.error(f"抓取文章失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def summarize_article(
        url: str,
        method: str = "simple",
        max_length: int = 500,
    ) -> dict[str, object]:
        """Fetch and summarize a supported article."""
        try:
            url = MCPInputValidator.validate_url(url)
            method = MCPInputValidator.validate_method(method)
            max_length = MCPInputValidator.validate_max_length(max_length)
            payload = await asyncio.to_thread(
                get_service().summarize,
                url,
                method,
                max_length,
            )
            return {
                "success": True,
                "title": payload.article.title,
                "author": payload.article.author,
                "word_count": payload.article.word_count,
                "summary": {
                    "content": payload.summary.content,
                    "key_points": list(payload.summary.key_points),
                    "tags": list(payload.summary.tags),
                    "method": payload.summary.method,
                    "model_name": payload.summary.model_name,
                },
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
        except Exception as exc:
            logger.error(f"摘要生成失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def get_article_info(url: str) -> dict[str, object]:
        """Fetch article metadata and a short preview."""
        try:
            url = MCPInputValidator.validate_url(url)
            payload = await asyncio.to_thread(get_service().get_info, url)
            return {
                "success": True,
                "title": payload.title,
                "author": payload.author,
                "account_name": payload.account_name,
                "publish_time": payload.publish_time,
                "word_count": payload.word_count,
                "preview": payload.preview,
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
        except Exception as exc:
            logger.error(f"获取文章信息失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def batch_summarize(
        urls: list[str],
        method: str = "simple",
        max_length: int = 300,
    ) -> dict[str, object]:
        """Batch summarize multiple supported articles."""
        try:
            urls = MCPInputValidator.validate_urls(urls)
            method = MCPInputValidator.validate_method(method)
            max_length = MCPInputValidator.validate_max_length(max_length)
            payload = await asyncio.to_thread(
                get_service().batch_summarize,
                urls,
                method,
                max_length,
            )
            return {
                "total": payload.total,
                "processed": payload.processed,
                "results": [
                    {
                        "url": item.url,
                        "success": item.success,
                        **({"title": item.title} if item.title is not None else {}),
                        **({"summary": item.summary} if item.summary is not None else {}),
                        **({"tags": list(item.tags)} if item.tags else {}),
                        **({"error": item.error} if item.error is not None else {}),
                    }
                    for item in payload.results
                ],
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def list_available_methods() -> dict[str, object]:
        """List available summarization methods."""
        methods = await asyncio.to_thread(get_service().list_available_methods)
        return {
            "methods": methods,
            "descriptions": _METHOD_DESCRIPTIONS,
        }
