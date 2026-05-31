"""Analysis and admin MCP toolset."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger

from ...features.analysis_workflow import AnalysisWorkflowService
from ..input_validator import MCPInputValidator, MCPValidationError
from ..responses import validation_error_response
from ..security import PermissionLevel, require_permission
from ..security_config import get_max_audit_logs, get_max_text_length, get_max_topic_length

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


AnalysisWorkflowFactory = Callable[[], AnalysisWorkflowService]


def register_analysis_tools(
    mcp_instance: FastMCP,
    service_factory: AnalysisWorkflowFactory,
) -> None:
    """Register analysis and admin tools on an MCP server."""
    get_service = service_factory

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def graph_analyze(url: str) -> dict[str, Any]:
        """Analyze an article and build a knowledge graph."""
        try:
            url = MCPInputValidator.validate_url(url)
            payload = await asyncio.to_thread(get_service().graph_analyze, url)

            return {
                "success": True,
                "title": payload.title,
                "graph_stats": {
                    "entity_count": payload.graph_stats.entity_count,
                    "relationship_count": payload.graph_stats.relationship_count,
                    "community_count": payload.graph_stats.community_count,
                },
                "entities": [
                    {"id": entity.id, "name": entity.name, "type": entity.type}
                    for entity in payload.entities
                ],
                "relationships": [
                    {
                        "source": relationship.source,
                        "target": relationship.target,
                        "type": relationship.type,
                    }
                    for relationship in payload.relationships
                ],
                "communities": [
                    {
                        "id": community.id,
                        "title": community.title,
                        "entity_count": community.entity_count,
                        "summary": community.summary,
                    }
                    for community in payload.communities
                ],
            }
        except MCPValidationError as exc:
            return validation_error_response(exc)
        except Exception as exc:
            logger.error(f"知识图谱分析失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def compare_articles(
        urls: list[str],
        aspects: list[str] | None = None,
    ) -> dict[str, Any]:
        """Compare multiple articles by entities, tags, and summaries."""
        try:
            urls = MCPInputValidator.validate_urls(urls)
            aspects = MCPInputValidator.validate_aspects(aspects)

            if len(urls) < 2:
                return {"success": False, "error": "至少需要 2 篇文章进行对比"}

            payload = await asyncio.to_thread(get_service().compare_articles, urls, aspects)

            return {
                "success": True,
                "article_count": payload.article_count,
                "articles": [
                    {
                        "url": article.url,
                        "title": article.title,
                        "author": article.author,
                        "word_count": article.word_count,
                        "summary": article.summary,
                        "tags": list(article.tags),
                        "entities": [
                            {"name": entity.name, "type": entity.type}
                            for entity in article.entities
                        ],
                    }
                    for article in payload.articles
                ],
                "comparison": {
                    "common_entities": list(payload.comparison.common_entities),
                    "common_tags": list(payload.comparison.common_tags),
                    "total_word_count": payload.comparison.total_word_count,
                    "avg_word_count": payload.comparison.avg_word_count,
                },
            }
        except MCPValidationError as exc:
            return validation_error_response(exc)
        except Exception as exc:
            logger.error(f"文章对比分析失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def track_topic(
        urls: list[str],
        topic: str,
    ) -> dict[str, Any]:
        """Track how a topic appears across multiple articles."""
        try:
            urls = MCPInputValidator.validate_urls(urls)
            topic = MCPInputValidator.sanitize_text(topic, max_length=get_max_topic_length())
            payload = await asyncio.to_thread(get_service().track_topic, urls, topic)

            return {
                "success": True,
                "topic": payload.topic,
                "total_articles": payload.total_articles,
                "articles_with_topic": payload.articles_with_topic,
                "total_occurrences": payload.total_occurrences,
                "results": [
                    {
                        "url": item.url,
                        "title": item.title,
                        "publish_time": item.publish_time,
                        "topic_occurrences": item.topic_occurrences,
                        "relevant_excerpts": list(item.relevant_excerpts),
                        "relevance_score": item.relevance_score,
                    }
                    for item in payload.results
                ],
            }
        except MCPValidationError as exc:
            return validation_error_response(exc)
        except Exception as exc:
            logger.error(f"主题追踪失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def evaluate_summary(
        url: str,
        summary_text: str | None = None,
        method: str = "simple",
    ) -> dict[str, Any]:
        """Evaluate summary quality for an article."""
        try:
            url = MCPInputValidator.validate_url(url)
            method = MCPInputValidator.validate_method(method)
            if summary_text is not None:
                summary_text = MCPInputValidator.sanitize_text(
                    summary_text,
                    max_length=get_max_text_length(),
                )

            payload = await asyncio.to_thread(
                get_service().evaluate_summary,
                url,
                summary_text,
                method,
            )

            return {
                "success": True,
                "title": payload.title,
                "original_length": payload.original_length,
                "summary_length": payload.summary_length,
                "compression_ratio": payload.compression_ratio,
                "evaluation": {
                    "keyword_coverage": payload.evaluation.keyword_coverage,
                    "conciseness_score": payload.evaluation.conciseness_score,
                    "overall_score": payload.evaluation.overall_score,
                    "covered_keywords": list(payload.evaluation.covered_keywords),
                },
                "summary": payload.summary,
                "recommendations": list(payload.recommendations),
            }
        except MCPValidationError as exc:
            return validation_error_response(exc)
        except Exception as exc:
            logger.error(f"摘要评估失败: {exc}")
            return {"success": False, "error": str(exc)}

    @mcp_instance.tool()
    @require_permission(PermissionLevel.ADMIN)
    async def get_audit_logs(limit: int = 50) -> dict[str, Any]:
        """Fetch MCP audit logs."""
        from ..security import get_security_manager

        try:
            limit = MCPInputValidator.validate_int_range(
                limit,
                field_name="limit",
                lower=1,
                upper=get_max_audit_logs(),
            )
            manager = get_security_manager()
            if manager.audit_logger is None:
                return {"success": False, "error": "审计日志未启用"}

            logs = manager.audit_logger.get_recent_logs(limit)
            return {"success": True, "count": len(logs), "logs": logs}
        except MCPValidationError as exc:
            return validation_error_response(exc)
        except Exception as exc:
            logger.error(f"获取审计日志失败: {exc}")
            return {"success": False, "error": str(exc)}
