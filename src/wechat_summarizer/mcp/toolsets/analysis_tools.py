"""Analysis and admin MCP toolset."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, cast

from loguru import logger

from ..input_validator import MCPInputValidator, MCPValidationError
from ..security import PermissionLevel, require_permission

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_analysis_tools(mcp_instance: FastMCP) -> None:
    """Register analysis and admin tools on an MCP server."""

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def graph_analyze(url: str) -> dict[str, Any]:
        """Analyze an article and build a knowledge graph."""
        from ...domain.value_objects import ArticleContent
        from ...infrastructure.config import get_container

        try:
            url = MCPInputValidator.validate_url(url)
            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)

            graphrag_summarizers = [
                name for name in container.summarizers if name.startswith("graphrag-")
            ]

            if not graphrag_summarizers:
                from ...infrastructure.adapters.knowledge_graph import (
                    SimpleCommunityDetector,
                    SimpleEntityExtractor,
                    SimpleGraphBuilder,
                )

                extractor = SimpleEntityExtractor()
                builder = SimpleGraphBuilder()
                detector = SimpleCommunityDetector()

                content = ArticleContent(text=article.content_text)
                extraction = await asyncio.to_thread(extractor.extract, content.text)
                kg = await asyncio.to_thread(builder.build, [extraction])
                communities = await asyncio.to_thread(detector.detect, kg)

                for community in communities:
                    kg.add_community(community)
            else:
                summarizer = cast(Any, container.summarizers[graphrag_summarizers[0]])
                content = ArticleContent(text=article.content_text)
                await asyncio.to_thread(summarizer.summarize, content)
                kg = summarizer.get_knowledge_graph()

            return {
                "success": True,
                "title": article.title,
                "graph_stats": {
                    "entity_count": kg.entity_count,
                    "relationship_count": kg.relationship_count,
                    "community_count": kg.community_count,
                },
                "entities": [
                    {"id": entity.id, "name": entity.name, "type": entity.type}
                    for entity in list(kg.entities.values())[:20]
                ],
                "relationships": [
                    {
                        "source": source_entity.name
                        if (source_entity := kg.get_entity(relationship.source_id))
                        else relationship.source_id,
                        "target": target_entity.name
                        if (target_entity := kg.get_entity(relationship.target_id))
                        else relationship.target_id,
                        "type": relationship.type,
                    }
                    for relationship in list(kg.relationships.values())[:30]
                ],
                "communities": [
                    {
                        "id": community.id,
                        "title": community.title,
                        "entity_count": len(community.entity_ids),
                        "summary": community.summary[:200] if community.summary else None,
                    }
                    for community in list(kg.communities.values())[:10]
                ],
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
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
        from ...infrastructure.adapters.knowledge_graph import SimpleEntityExtractor
        from ...infrastructure.config import get_container

        try:
            urls = MCPInputValidator.validate_urls(urls, max_count=5)
            aspects = MCPInputValidator.validate_aspects(aspects)
            _ = aspects

            if len(urls) < 2:
                return {"success": False, "error": "至少需要 2 篇文章进行对比"}

            container = get_container()
            extractor = SimpleEntityExtractor()
            articles_data: list[dict[str, Any]] = []

            for url in urls:
                article = await asyncio.to_thread(container.fetch_use_case.execute, url)
                extraction = await asyncio.to_thread(extractor.extract, article.content_text)
                summary = await asyncio.to_thread(
                    container.summarize_use_case.execute,
                    article,
                    method="simple",
                    max_length=200,
                )

                articles_data.append(
                    {
                        "url": url,
                        "title": article.title,
                        "author": article.author,
                        "word_count": article.word_count,
                        "summary": summary.content,
                        "tags": list(summary.tags),
                        "entities": [
                            {"name": entity.name, "type": entity.type}
                            for entity in extraction.entities[:10]
                        ],
                    }
                )

            entity_name_sets: list[set[str]] = []
            tag_sets: list[set[str]] = []
            word_counts: list[int] = []
            for article_data in articles_data:
                entities = cast(list[dict[str, str]], article_data.get("entities", []))
                entity_name_sets.append({entity["name"] for entity in entities if "name" in entity})
                tags = cast(list[str], article_data.get("tags", []))
                tag_sets.append(set(tags))
                word_count_value = article_data.get("word_count")
                word_counts.append(word_count_value if isinstance(word_count_value, int) else 0)

            common_entities = set.intersection(*entity_name_sets) if entity_name_sets else set()
            common_tags = set.intersection(*tag_sets) if tag_sets else set()
            total_word_count = sum(word_counts)

            return {
                "success": True,
                "article_count": len(articles_data),
                "articles": articles_data,
                "comparison": {
                    "common_entities": list(common_entities),
                    "common_tags": list(common_tags),
                    "total_word_count": total_word_count,
                    "avg_word_count": total_word_count // len(articles_data),
                },
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
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
        import re

        from ...infrastructure.config import get_container

        try:
            urls = MCPInputValidator.validate_urls(urls)
            topic = MCPInputValidator.sanitize_text(topic, max_length=200)

            container = get_container()
            topic_data: list[dict[str, Any]] = []

            for url in urls:
                try:
                    article = await asyncio.to_thread(container.fetch_use_case.execute, url)
                    content = article.content_text.lower()
                    topic_lower = topic.lower()
                    occurrences = len(re.findall(re.escape(topic_lower), content))

                    paragraphs = article.content_text.split("\n")
                    relevant_paragraphs = [
                        paragraph.strip()[:200] + "..."
                        if len(paragraph) > 200
                        else paragraph.strip()
                        for paragraph in paragraphs
                        if topic_lower in paragraph.lower() and len(paragraph.strip()) > 20
                    ][:3]

                    topic_data.append(
                        {
                            "url": url,
                            "title": article.title,
                            "publish_time": article.publish_time_str,
                            "topic_occurrences": occurrences,
                            "relevant_excerpts": relevant_paragraphs,
                            "relevance_score": min(1.0, occurrences / 10),
                        }
                    )
                except Exception as exc:
                    topic_data.append({"url": url, "error": str(exc)})

            def _to_int(value: Any) -> int:
                return value if isinstance(value, int) else 0

            sorted_data = sorted(
                [item for item in topic_data if "error" not in item],
                key=lambda item: _to_int(item.get("topic_occurrences")),
                reverse=True,
            )

            articles_with_topic = len(
                [item for item in topic_data if _to_int(item.get("topic_occurrences")) > 0]
            )
            total_occurrences = sum(_to_int(item.get("topic_occurrences")) for item in topic_data)

            return {
                "success": True,
                "topic": topic,
                "total_articles": len(topic_data),
                "articles_with_topic": articles_with_topic,
                "total_occurrences": total_occurrences,
                "results": sorted_data,
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
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
        import re

        from ...infrastructure.config import get_container

        try:
            url = MCPInputValidator.validate_url(url)
            method = MCPInputValidator.validate_method(method)
            if summary_text is not None:
                summary_text = MCPInputValidator.sanitize_text(summary_text, max_length=20_000)

            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)

            if not summary_text:
                summary = await asyncio.to_thread(
                    container.summarize_use_case.execute,
                    article,
                    method=method,
                    max_length=500,
                )
                summary_text = summary.content

            original_length = len(article.content_text)
            summary_length = len(summary_text)
            compression_ratio = summary_length / original_length if original_length > 0 else 0

            words = re.findall(r"[\u4e00-\u9fff]+", article.content_text)
            word_freq: dict[str, int] = {}
            for word in words:
                if len(word) >= 2:
                    word_freq[word] = word_freq.get(word, 0) + 1

            top_words = sorted(word_freq.items(), key=lambda item: item[1], reverse=True)[:20]
            top_word_set = {word for word, _ in top_words}

            summary_words = set(re.findall(r"[\u4e00-\u9fff]+", summary_text))
            covered_words = top_word_set & summary_words
            keyword_coverage = len(covered_words) / len(top_word_set) if top_word_set else 0

            if 0.05 <= compression_ratio <= 0.15:
                conciseness_score = 1.0
            elif compression_ratio < 0.05:
                conciseness_score = compression_ratio / 0.05
            else:
                conciseness_score = max(0.0, 1 - (compression_ratio - 0.15) / 0.35)

            overall_score = keyword_coverage * 0.6 + conciseness_score * 0.4

            return {
                "success": True,
                "title": article.title,
                "original_length": original_length,
                "summary_length": summary_length,
                "compression_ratio": round(compression_ratio, 4),
                "evaluation": {
                    "keyword_coverage": round(keyword_coverage, 2),
                    "conciseness_score": round(conciseness_score, 2),
                    "overall_score": round(overall_score, 2),
                    "covered_keywords": list(covered_words)[:10],
                },
                "summary": summary_text[:500] + "..." if len(summary_text) > 500 else summary_text,
                "recommendations": _get_summary_recommendations(
                    keyword_coverage,
                    conciseness_score,
                    compression_ratio,
                ),
            }
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
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
                upper=100,
            )
            manager = get_security_manager()
            if manager.audit_logger is None:
                return {"success": False, "error": "审计日志未启用"}

            logs = manager.audit_logger.get_recent_logs(min(limit, 100))
            return {"success": True, "count": len(logs), "logs": logs}
        except MCPValidationError as exc:
            return {"success": False, "error": f"参数校验失败: {exc}"}
        except Exception as exc:
            logger.error(f"获取审计日志失败: {exc}")
            return {"success": False, "error": str(exc)}


def _get_summary_recommendations(
    keyword_coverage: float,
    conciseness_score: float,
    compression_ratio: float,
) -> list[str]:
    """Generate summary-quality recommendations from evaluation scores."""
    recommendations: list[str] = []

    if keyword_coverage < 0.5:
        recommendations.append("摘要应包含更多原文关键信息")
    if conciseness_score < 0.5:
        if compression_ratio > 0.20:
            recommendations.append("摘要过长，建议精简内容")
        elif compression_ratio < 0.03:
            recommendations.append("摘要过短，可能遗漏重要信息")

    if not recommendations:
        recommendations.append("摘要质量良好")

    return recommendations
