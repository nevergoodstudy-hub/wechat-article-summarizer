"""DTOs for MCP-facing analysis workflows."""

from __future__ import annotations

from dataclasses import dataclass

from ..article_workflow import ArticleMetadataPayload, SummaryPayload


@dataclass(frozen=True)
class GraphEntityPayload:
    """Knowledge-graph entity prepared for delivery layers."""

    id: str
    name: str
    type: str


@dataclass(frozen=True)
class GraphRelationshipPayload:
    """Knowledge-graph relationship prepared for delivery layers."""

    source: str
    target: str
    type: str


@dataclass(frozen=True)
class GraphCommunityPayload:
    """Knowledge-graph community prepared for delivery layers."""

    id: str
    title: str
    entity_count: int
    summary: str | None


@dataclass(frozen=True)
class GraphStatsPayload:
    """Knowledge-graph aggregate counts."""

    entity_count: int
    relationship_count: int
    community_count: int


@dataclass(frozen=True)
class GraphAnalysisPayload:
    """Graph analysis result for an article."""

    title: str
    graph_stats: GraphStatsPayload
    entities: tuple[GraphEntityPayload, ...]
    relationships: tuple[GraphRelationshipPayload, ...]
    communities: tuple[GraphCommunityPayload, ...]


@dataclass(frozen=True)
class ComparedArticlePayload:
    """Single article projection in a comparison result."""

    url: str
    title: str
    author: str | None
    word_count: int
    summary: str
    tags: tuple[str, ...]
    entities: tuple[GraphEntityPayload, ...]


@dataclass(frozen=True)
class ArticleComparisonStatsPayload:
    """Aggregate article comparison metrics."""

    common_entities: tuple[str, ...]
    common_tags: tuple[str, ...]
    total_word_count: int
    avg_word_count: int


@dataclass(frozen=True)
class ArticleComparisonPayload:
    """Comparison result for multiple articles."""

    article_count: int
    articles: tuple[ComparedArticlePayload, ...]
    comparison: ArticleComparisonStatsPayload


@dataclass(frozen=True)
class TopicTrackingItemPayload:
    """Topic tracking result for one article."""

    url: str
    title: str | None = None
    publish_time: str | None = None
    topic_occurrences: int | None = None
    relevant_excerpts: tuple[str, ...] = ()
    relevance_score: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class TopicTrackingPayload:
    """Topic tracking result across multiple articles."""

    topic: str
    total_articles: int
    articles_with_topic: int
    total_occurrences: int
    results: tuple[TopicTrackingItemPayload, ...]


@dataclass(frozen=True)
class SummaryEvaluationMetricsPayload:
    """Summary quality metrics."""

    keyword_coverage: float
    conciseness_score: float
    overall_score: float
    covered_keywords: tuple[str, ...]


@dataclass(frozen=True)
class SummaryEvaluationPayload:
    """Summary evaluation result."""

    title: str
    original_length: int
    summary_length: int
    compression_ratio: float
    evaluation: SummaryEvaluationMetricsPayload
    summary: str
    recommendations: tuple[str, ...]
    article: ArticleMetadataPayload | None = None
    generated_summary: SummaryPayload | None = None
