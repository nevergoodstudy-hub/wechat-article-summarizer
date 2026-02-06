"""MCP 服务器实现

提供以下工具给 AI Agent：
- fetch_article: 抓取文章
- summarize_article: 抓取并摘要文章
- get_article_info: 获取文章基本信息
- batch_summarize: 批量摘要文章

提供以下资源：
- article://{url}: 文章内容资源
"""

from __future__ import annotations

import asyncio
from typing import Any

from loguru import logger

from .security import PermissionLevel, require_permission

# 延迟导入 MCP SDK（可选依赖）
_mcp_available = True
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    _mcp_available = False
    FastMCP = None  # type: ignore


def _get_mcp() -> "FastMCP":
    """获取 MCP 实例"""
    if not _mcp_available:
        raise ImportError(
            "MCP SDK 未安装。请运行: pip install mcp>=1.2.0"
        )
    return FastMCP("WeChat Article Summarizer")


# 创建 MCP 实例（延迟初始化）
mcp: "FastMCP | None" = None


def _ensure_mcp() -> "FastMCP":
    """确保 MCP 实例已创建"""
    global mcp
    if mcp is None:
        mcp = _get_mcp()
        _register_tools(mcp)
        _register_resources(mcp)
    return mcp


def _register_tools(mcp_instance: "FastMCP") -> None:
    """注册 MCP 工具"""
    
    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def fetch_article(url: str) -> dict[str, Any]:
        """抓取微信公众号或其他支持的文章
        
        Args:
            url: 文章 URL（支持微信公众号、知乎、头条等）
        
        Returns:
            文章信息，包含标题、作者、内容等
        """
        from ..infrastructure.config import get_container
        
        try:
            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)
            
            return {
                "success": True,
                "title": article.title,
                "author": article.author,
                "account_name": article.account_name,
                "publish_time": article.publish_time_str,
                "word_count": article.word_count,
                "content": article.content_text[:10000],  # 限制长度
                "content_truncated": len(article.content_text) > 10000,
            }
        except Exception as e:
            logger.error(f"抓取文章失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def summarize_article(
        url: str,
        method: str = "simple",
        max_length: int = 500,
    ) -> dict[str, Any]:
        """抓取并摘要文章
        
        Args:
            url: 文章 URL
            method: 摘要方法 (simple, ollama, openai, anthropic, zhipu, deepseek, textrank)
            max_length: 摘要最大长度
        
        Returns:
            文章摘要信息
        """
        from ..infrastructure.config import get_container
        
        try:
            container = get_container()
            
            # 抓取文章
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)
            
            # 生成摘要
            summary = await asyncio.to_thread(
                container.summarize_use_case.execute,
                article, 
                method=method,
                max_length=max_length,
            )
            article.attach_summary(summary)
            
            return {
                "success": True,
                "title": article.title,
                "author": article.author,
                "word_count": article.word_count,
                "summary": {
                    "content": summary.content,
                    "key_points": list(summary.key_points),
                    "tags": list(summary.tags),
                    "method": summary.method.value,
                    "model_name": summary.model_name,
                },
            }
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def get_article_info(url: str) -> dict[str, Any]:
        """获取文章基本信息（不含完整内容）
        
        Args:
            url: 文章 URL
        
        Returns:
            文章基本信息
        """
        from ..infrastructure.config import get_container
        
        try:
            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)
            
            # 提取前几段作为预览
            preview = article.content_text[:500]
            if len(article.content_text) > 500:
                preview += "..."
            
            return {
                "success": True,
                "title": article.title,
                "author": article.author,
                "account_name": article.account_name,
                "publish_time": article.publish_time_str,
                "word_count": article.word_count,
                "preview": preview,
            }
        except Exception as e:
            logger.error(f"获取文章信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def batch_summarize(
        urls: list[str],
        method: str = "simple",
        max_length: int = 300,
    ) -> dict[str, Any]:
        """批量摘要多篇文章
        
        Args:
            urls: 文章 URL 列表
            method: 摘要方法
            max_length: 单篇摘要最大长度
        
        Returns:
            批量摘要结果
        """
        from ..infrastructure.config import get_container
        
        container = get_container()
        results = []
        
        for url in urls[:10]:  # 限制最多 10 篇
            try:
                article = await asyncio.to_thread(container.fetch_use_case.execute, url)
                summary = await asyncio.to_thread(
                    container.summarize_use_case.execute,
                    article,
                    method=method,
                    max_length=max_length,
                )
                
                results.append({
                    "url": url,
                    "success": True,
                    "title": article.title,
                    "summary": summary.content,
                    "tags": list(summary.tags),
                })
            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e),
                })
        
        return {
            "total": len(urls),
            "processed": len(results),
            "results": results,
        }
    
    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def list_available_methods() -> dict[str, Any]:
        """列出所有可用的摘要方法
        
        Returns:
            可用摘要方法列表
        """
        from ..infrastructure.config import get_container
        
        container = get_container()
        methods = list(container.summarizers.keys())
        
        return {
            "methods": methods,
            "descriptions": {
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
        }

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def graph_analyze(url: str) -> dict[str, Any]:
        """分析文章并构建知识图谱

        使用 GraphRAG 技术提取文章中的实体、关系，并构建知识图谱。

        Args:
            url: 文章 URL

        Returns:
            知识图谱分析结果，包含实体、关系、社区信息
        """
        from ..infrastructure.config import get_container
        from ..domain.value_objects import ArticleContent

        try:
            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)

            # 尝试使用 GraphRAG 摘要器
            graphrag_summarizers = [
                name for name in container.summarizers
                if name.startswith("graphrag-")
            ]

            if not graphrag_summarizers:
                # 使用简单实体提取
                from ..infrastructure.adapters.knowledge_graph import (
                    SimpleEntityExtractor,
                    SimpleGraphBuilder,
                    SimpleCommunityDetector,
                )

                extractor = SimpleEntityExtractor()
                builder = SimpleGraphBuilder()
                detector = SimpleCommunityDetector()

                content = ArticleContent(text=article.content_text)
                extraction = await asyncio.to_thread(extractor.extract, content.text)
                kg = await asyncio.to_thread(builder.build, [extraction])
                communities = await asyncio.to_thread(detector.detect, kg)

                for comm in communities:
                    kg.add_community(comm)
            else:
                # 使用 GraphRAG 摘要器
                summarizer = container.summarizers[graphrag_summarizers[0]]
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
                    {"id": e.id, "name": e.name, "type": e.type}
                    for e in list(kg.entities.values())[:20]  # 限制数量
                ],
                "relationships": [
                    {
                        "source": kg.get_entity(r.source_id).name if kg.get_entity(r.source_id) else r.source_id,
                        "target": kg.get_entity(r.target_id).name if kg.get_entity(r.target_id) else r.target_id,
                        "type": r.type,
                    }
                    for r in list(kg.relationships.values())[:30]  # 限制数量
                ],
                "communities": [
                    {
                        "id": c.id,
                        "title": c.title,
                        "entity_count": len(c.entity_ids),
                        "summary": c.summary[:200] if c.summary else None,
                    }
                    for c in list(kg.communities.values())[:10]
                ],
            }
        except Exception as e:
            logger.error(f"知识图谱分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def compare_articles(
        urls: list[str],
        aspects: list[str] | None = None,
    ) -> dict[str, Any]:
        """对比分析多篇文章

        比较多篇文章的主题、观点、关键实体等。

        Args:
            urls: 文章 URL 列表（2-5篇）
            aspects: 对比维度（默认: ["主题", "观点", "实体"]）

        Returns:
            对比分析结果
        """
        from ..infrastructure.config import get_container
        from ..infrastructure.adapters.knowledge_graph import SimpleEntityExtractor

        if len(urls) < 2:
            return {"success": False, "error": "至少需要 2 篇文章进行对比"}
        if len(urls) > 5:
            urls = urls[:5]  # 限制最多 5 篇

        aspects = aspects or ["主题", "观点", "实体"]
        container = get_container()
        extractor = SimpleEntityExtractor()

        articles_data = []

        try:
            for url in urls:
                article = await asyncio.to_thread(container.fetch_use_case.execute, url)
                extraction = await asyncio.to_thread(extractor.extract, article.content_text)

                # 生成简短摘要
                summary = await asyncio.to_thread(
                    container.summarize_use_case.execute,
                    article, method="simple", max_length=200,
                )

                articles_data.append({
                    "url": url,
                    "title": article.title,
                    "author": article.author,
                    "word_count": article.word_count,
                    "summary": summary.content,
                    "tags": list(summary.tags),
                    "entities": [
                        {"name": e.name, "type": e.type}
                        for e in extraction.entities[:10]
                    ],
                })

            # 找出共同实体
            all_entity_names = [
                set(e["name"] for e in a["entities"])
                for a in articles_data
            ]
            common_entities = set.intersection(*all_entity_names) if all_entity_names else set()

            # 找出共同标签
            all_tags = [set(a["tags"]) for a in articles_data]
            common_tags = set.intersection(*all_tags) if all_tags else set()

            return {
                "success": True,
                "article_count": len(articles_data),
                "articles": articles_data,
                "comparison": {
                    "common_entities": list(common_entities),
                    "common_tags": list(common_tags),
                    "total_word_count": sum(a["word_count"] for a in articles_data),
                    "avg_word_count": sum(a["word_count"] for a in articles_data) // len(articles_data),
                },
            }
        except Exception as e:
            logger.error(f"文章对比分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def track_topic(
        urls: list[str],
        topic: str,
    ) -> dict[str, Any]:
        """追踪特定主题在多篇文章中的演变

        分析特定主题在多篇文章中的出现情况和变化趋势。

        Args:
            urls: 文章 URL 列表
            topic: 要追踪的主题关键词

        Returns:
            主题追踪结果
        """
        from ..infrastructure.config import get_container
        import re

        container = get_container()
        topic_data = []

        try:
            for url in urls[:10]:  # 限制最多 10 篇
                try:
                    article = await asyncio.to_thread(container.fetch_use_case.execute, url)

                    # 统计主题出现次数
                    content = article.content_text.lower()
                    topic_lower = topic.lower()
                    occurrences = len(re.findall(re.escape(topic_lower), content))

                    # 提取包含主题的段落
                    paragraphs = article.content_text.split("\n")
                    relevant_paragraphs = [
                        p.strip()[:200] + "..." if len(p) > 200 else p.strip()
                        for p in paragraphs
                        if topic_lower in p.lower() and len(p.strip()) > 20
                    ][:3]  # 最多 3 个段落

                    topic_data.append({
                        "url": url,
                        "title": article.title,
                        "publish_time": article.publish_time_str,
                        "topic_occurrences": occurrences,
                        "relevant_excerpts": relevant_paragraphs,
                        "relevance_score": min(1.0, occurrences / 10),  # 简单相关度评分
                    })
                except Exception as e:
                    topic_data.append({
                        "url": url,
                        "error": str(e),
                    })

            # 按相关度排序
            sorted_data = sorted(
                [d for d in topic_data if "error" not in d],
                key=lambda x: x["topic_occurrences"],
                reverse=True,
            )

            return {
                "success": True,
                "topic": topic,
                "total_articles": len(topic_data),
                "articles_with_topic": len([d for d in topic_data if d.get("topic_occurrences", 0) > 0]),
                "total_occurrences": sum(d.get("topic_occurrences", 0) for d in topic_data),
                "results": sorted_data,
            }
        except Exception as e:
            logger.error(f"主题追踪失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @mcp_instance.tool()
    @require_permission(PermissionLevel.READ)
    async def evaluate_summary(
        url: str,
        summary_text: str | None = None,
        method: str = "simple",
    ) -> dict[str, Any]:
        """评估摘要质量

        评估摘要的准确性、完整性和简洁性。

        Args:
            url: 原文章 URL
            summary_text: 待评估的摘要（如果为空，则先生成摘要）
            method: 生成摘要的方法（当 summary_text 为空时使用）

        Returns:
            摘要质量评估结果
        """
        from ..infrastructure.config import get_container

        try:
            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)

            # 如果没有提供摘要，先生成一个
            if not summary_text:
                summary = await asyncio.to_thread(
                    container.summarize_use_case.execute,
                    article, method=method, max_length=500,
                )
                summary_text = summary.content

            # 评估指标
            original_length = len(article.content_text)
            summary_length = len(summary_text)
            compression_ratio = summary_length / original_length if original_length > 0 else 0

            # 关键词覆盖度（简单评估）
            # 提取原文高频词
            import re
            words = re.findall(r'[\u4e00-\u9fff]+', article.content_text)
            word_freq = {}
            for w in words:
                if len(w) >= 2:
                    word_freq[w] = word_freq.get(w, 0) + 1

            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            top_word_set = set(w for w, _ in top_words)

            # 检查摘要中包含多少高频词
            summary_words = set(re.findall(r'[\u4e00-\u9fff]+', summary_text))
            covered_words = top_word_set & summary_words
            keyword_coverage = len(covered_words) / len(top_word_set) if top_word_set else 0

            # 简洁性评分（基于压缩率）
            # 理想压缩率在 5%-15% 之间
            if 0.05 <= compression_ratio <= 0.15:
                conciseness_score = 1.0
            elif compression_ratio < 0.05:
                conciseness_score = compression_ratio / 0.05
            else:
                conciseness_score = max(0, 1 - (compression_ratio - 0.15) / 0.35)

            # 综合评分
            overall_score = (keyword_coverage * 0.6 + conciseness_score * 0.4)

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
                    keyword_coverage, conciseness_score, compression_ratio
                ),
            }
        except Exception as e:
            logger.error(f"摘要评估失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @mcp_instance.tool()
    @require_permission(PermissionLevel.ADMIN)
    async def get_audit_logs(limit: int = 50) -> dict[str, Any]:
        """获取 MCP 调用审计日志

        需要管理员权限。

        Args:
            limit: 返回日志条数（最多 100）

        Returns:
            审计日志列表
        """
        from .security import get_security_manager

        try:
            manager = get_security_manager()
            if manager.audit_logger is None:
                return {
                    "success": False,
                    "error": "审计日志未启用",
                }

            logs = manager.audit_logger.get_recent_logs(min(limit, 100))
            return {
                "success": True,
                "count": len(logs),
                "logs": logs,
            }
        except Exception as e:
            logger.error(f"获取审计日志失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }


def _get_summary_recommendations(
    keyword_coverage: float,
    conciseness_score: float,
    compression_ratio: float,
) -> list[str]:
    """根据评估结果生成改进建议"""
    recommendations = []

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


def _register_resources(mcp_instance: "FastMCP") -> None:
    """注册 MCP 资源"""
    
    @mcp_instance.resource("article://{url}")
    async def get_article_content(url: str) -> str:
        """获取文章内容作为资源
        
        可用于 RAG 或上下文增强。
        """
        from ..infrastructure.config import get_container
        
        try:
            container = get_container()
            article = await asyncio.to_thread(container.fetch_use_case.execute, url)
            
            # 格式化为 Markdown
            content = f"""# {article.title}

**作者**: {article.author or "未知"}
**来源**: {article.account_name or "未知"}
**发布时间**: {article.publish_time_str}
**字数**: {article.word_count}

---

{article.content_text}
"""
            return content
        except Exception as e:
            return f"获取文章失败: {e}"


def run_mcp_server(transport: str = "stdio", port: int = 8000) -> None:
    """运行 MCP 服务器
    
    Args:
        transport: 传输方式 ("stdio" 或 "http")
        port: HTTP 模式端口号
    """
    mcp_instance = _ensure_mcp()
    
    logger.info(f"启动 MCP 服务器 (transport={transport})")
    
    if transport == "stdio":
        mcp_instance.run(transport="stdio")
    elif transport == "http":
        # HTTP 模式需要额外配置
        import uvicorn
        from starlette.applications import Starlette
        from starlette.routing import Mount
        
        app = Starlette(
            routes=[
                Mount("/mcp", app=mcp_instance.sse_app()),
            ]
        )
        uvicorn.run(app, host="0.0.0.0", port=port)
    else:
        raise ValueError(f"不支持的传输方式: {transport}")


# 模块入口
if __name__ == "__main__":
    run_mcp_server()
