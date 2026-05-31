"""Feature service for article analysis workflows."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol, cast

from ...domain.value_objects import ArticleContent
from .dto import (
    ArticleComparisonPayload,
    ArticleComparisonStatsPayload,
    ComparedArticlePayload,
    GraphAnalysisPayload,
    GraphCommunityPayload,
    GraphEntityPayload,
    GraphRelationshipPayload,
    GraphStatsPayload,
    SummaryEvaluationMetricsPayload,
    SummaryEvaluationPayload,
    TopicTrackingItemPayload,
    TopicTrackingPayload,
)

if TYPE_CHECKING:
    from ...application.ports.outbound import (
        CommunityDetectorPort,
        EntityExtractorPort,
        GraphBuilderPort,
        KnowledgeGraph,
        SummarizerPort,
    )
    from ...application.use_cases.fetch_article import FetchArticleUseCase
    from ...application.use_cases.summarize_article import SummarizeArticleUseCase
    from ...domain.entities import Article, Summary


class _GraphRAGSummarizerLike(Protocol):
    """Summarizer surface needed to retrieve a generated knowledge graph."""

    def summarize(self, content: ArticleContent) -> Summary: ...

    def get_knowledge_graph(self) -> KnowledgeGraph | None: ...


class AnalysisWorkflowService:
    """Application-facing service for analysis and MCP delivery workflows."""

    def __init__(
        self,
        fetch_use_case: FetchArticleUseCase,
        summarize_use_case: SummarizeArticleUseCase,
        entity_extractor: EntityExtractorPort,
        graph_builder: GraphBuilderPort,
        community_detector: CommunityDetectorPort,
        summarizers: dict[str, SummarizerPort] | None = None,
    ) -> None:
        self._fetch_use_case = fetch_use_case
        self._summarize_use_case = summarize_use_case
        self._entity_extractor = entity_extractor
        self._graph_builder = graph_builder
        self._community_detector = community_detector
        self._summarizers = summarizers or {}

    def graph_analyze(self, url: str) -> GraphAnalysisPayload:
        """Fetch an article and project its knowledge graph."""
        article = self._fetch_use_case.execute(url)
        kg = self._build_knowledge_graph(article)

        return GraphAnalysisPayload(
            title=article.title,
            graph_stats=GraphStatsPayload(
                entity_count=kg.entity_count,
                relationship_count=kg.relationship_count,
                community_count=kg.community_count,
            ),
            entities=tuple(
                GraphEntityPayload(id=entity.id, name=entity.name, type=entity.type)
                for entity in list(kg.entities.values())[:20]
            ),
            relationships=tuple(
                GraphRelationshipPayload(
                    source=source_entity.name
                    if (source_entity := kg.get_entity(relationship.source_id))
                    else relationship.source_id,
                    target=target_entity.name
                    if (target_entity := kg.get_entity(relationship.target_id))
                    else relationship.target_id,
                    type=relationship.type,
                )
                for relationship in list(kg.relationships.values())[:30]
            ),
            communities=tuple(
                GraphCommunityPayload(
                    id=community.id,
                    title=community.title,
                    entity_count=len(community.entity_ids),
                    summary=community.summary[:200] if community.summary else None,
                )
                for community in list(kg.communities.values())[:10]
            ),
        )

    def compare_articles(
        self,
        urls: list[str],
        aspects: list[str] | None = None,
    ) -> ArticleComparisonPayload:
        """Compare articles by summaries, tags, entities, and size."""
        _ = aspects
        if len(urls) < 2:
            raise ValueError("至少需要 2 篇文章进行对比")

        articles: list[ComparedArticlePayload] = []
        entity_name_sets: list[set[str]] = []
        tag_sets: list[set[str]] = []
        total_word_count = 0

        for url in urls:
            article = self._fetch_use_case.execute(url)
            extraction = self._entity_extractor.extract(article.content_text)
            summary = self._summarize_use_case.execute(
                article,
                method="simple",
                max_length=200,
            )

            entities = tuple(
                GraphEntityPayload(id=entity.id, name=entity.name, type=entity.type)
                for entity in extraction.entities[:10]
            )
            tags = tuple(summary.tags)

            articles.append(
                ComparedArticlePayload(
                    url=url,
                    title=article.title,
                    author=article.author,
                    word_count=article.word_count,
                    summary=summary.content,
                    tags=tags,
                    entities=entities,
                )
            )
            entity_name_sets.append({entity.name for entity in entities})
            tag_sets.append(set(tags))
            total_word_count += article.word_count

        common_entities = set.intersection(*entity_name_sets) if entity_name_sets else set()
        common_tags = set.intersection(*tag_sets) if tag_sets else set()

        return ArticleComparisonPayload(
            article_count=len(articles),
            articles=tuple(articles),
            comparison=ArticleComparisonStatsPayload(
                common_entities=tuple(sorted(common_entities)),
                common_tags=tuple(sorted(common_tags)),
                total_word_count=total_word_count,
                avg_word_count=total_word_count // len(articles),
            ),
        )

    def track_topic(self, urls: list[str], topic: str) -> TopicTrackingPayload:
        """Track how often a topic appears across multiple articles."""
        topic_data: list[TopicTrackingItemPayload] = []
        topic_lower = topic.lower()

        for url in urls:
            try:
                article = self._fetch_use_case.execute(url)
                content = article.content_text.lower()
                occurrences = len(re.findall(re.escape(topic_lower), content))
                relevant_paragraphs = self._find_relevant_paragraphs(
                    article.content_text,
                    topic_lower,
                )

                topic_data.append(
                    TopicTrackingItemPayload(
                        url=url,
                        title=article.title,
                        publish_time=article.publish_time_str,
                        topic_occurrences=occurrences,
                        relevant_excerpts=tuple(relevant_paragraphs),
                        relevance_score=min(1.0, occurrences / 10),
                    )
                )
            except Exception as exc:
                topic_data.append(TopicTrackingItemPayload(url=url, error=str(exc)))

        sorted_data = tuple(
            sorted(
                (item for item in topic_data if item.error is None),
                key=lambda item: item.topic_occurrences or 0,
                reverse=True,
            )
        )
        articles_with_topic = len(
            [item for item in topic_data if (item.topic_occurrences or 0) > 0]
        )
        total_occurrences = sum(item.topic_occurrences or 0 for item in topic_data)

        return TopicTrackingPayload(
            topic=topic,
            total_articles=len(topic_data),
            articles_with_topic=articles_with_topic,
            total_occurrences=total_occurrences,
            results=sorted_data,
        )

    def evaluate_summary(
        self,
        url: str,
        summary_text: str | None = None,
        method: str = "simple",
    ) -> SummaryEvaluationPayload:
        """Evaluate summary quality for an article."""
        article = self._fetch_use_case.execute(url)
        generated_summary: Summary | None = None

        if not summary_text:
            generated_summary = self._summarize_use_case.execute(
                article,
                method=method,
                max_length=500,
            )
            summary_text = generated_summary.content

        original_length = len(article.content_text)
        summary_length = len(summary_text)
        compression_ratio = summary_length / original_length if original_length > 0 else 0

        covered_words, keyword_coverage = self._keyword_coverage(
            article.content_text,
            summary_text,
        )
        conciseness_score = self._conciseness_score(compression_ratio)
        overall_score = keyword_coverage * 0.6 + conciseness_score * 0.4

        return SummaryEvaluationPayload(
            title=article.title,
            original_length=original_length,
            summary_length=summary_length,
            compression_ratio=round(compression_ratio, 4),
            evaluation=SummaryEvaluationMetricsPayload(
                keyword_coverage=round(keyword_coverage, 2),
                conciseness_score=round(conciseness_score, 2),
                overall_score=round(overall_score, 2),
                covered_keywords=tuple(sorted(covered_words)[:10]),
            ),
            summary=summary_text[:500] + "..." if len(summary_text) > 500 else summary_text,
            recommendations=tuple(
                self._get_summary_recommendations(
                    keyword_coverage,
                    conciseness_score,
                    compression_ratio,
                )
            ),
        )

    def _build_knowledge_graph(self, article: Article) -> KnowledgeGraph:
        graphrag_summarizer = self._get_graphrag_summarizer()
        content = ArticleContent(text=article.content_text)

        if graphrag_summarizer is not None:
            graphrag_summarizer.summarize(content)
            kg = graphrag_summarizer.get_knowledge_graph()
            if kg is not None:
                return kg

        extraction = self._entity_extractor.extract(content.text)
        kg = self._graph_builder.build([extraction])
        communities = self._community_detector.detect(kg)
        for community in communities:
            kg.add_community(community)
        return kg

    def _get_graphrag_summarizer(self) -> _GraphRAGSummarizerLike | None:
        for name, summarizer in self._summarizers.items():
            if name.startswith("graphrag-") and hasattr(summarizer, "get_knowledge_graph"):
                return cast("_GraphRAGSummarizerLike", summarizer)
        return None

    @staticmethod
    def _find_relevant_paragraphs(text: str, topic_lower: str) -> list[str]:
        paragraphs = text.split("\n")
        return [
            paragraph.strip()[:200] + "..." if len(paragraph) > 200 else paragraph.strip()
            for paragraph in paragraphs
            if topic_lower in paragraph.lower() and len(paragraph.strip()) > 20
        ][:3]

    @staticmethod
    def _keyword_coverage(article_text: str, summary_text: str) -> tuple[set[str], float]:
        words = re.findall(r"[\u4e00-\u9fff]+", article_text)
        word_freq: dict[str, int] = {}
        for word in words:
            if len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        top_words = sorted(word_freq.items(), key=lambda item: item[1], reverse=True)[:20]
        top_word_set = {word for word, _ in top_words}
        summary_words = set(re.findall(r"[\u4e00-\u9fff]+", summary_text))
        covered_words = top_word_set & summary_words
        keyword_coverage = len(covered_words) / len(top_word_set) if top_word_set else 0
        return covered_words, keyword_coverage

    @staticmethod
    def _conciseness_score(compression_ratio: float) -> float:
        if 0.05 <= compression_ratio <= 0.15:
            return 1.0
        if compression_ratio < 0.05:
            return compression_ratio / 0.05
        return max(0.0, 1 - (compression_ratio - 0.15) / 0.35)

    @staticmethod
    def _get_summary_recommendations(
        keyword_coverage: float,
        conciseness_score: float,
        compression_ratio: float,
    ) -> list[str]:
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
