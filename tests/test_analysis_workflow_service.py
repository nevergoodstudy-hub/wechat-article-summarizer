"""Tests for the analysis workflow vertical slice."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from wechat_summarizer.application.ports.outbound import (
    Community,
    Entity,
    ExtractionResult,
    KnowledgeGraph,
    Relationship,
)
from wechat_summarizer.domain.value_objects import ArticleContent
from wechat_summarizer.features.analysis_workflow import AnalysisWorkflowService


def _sample_graph() -> KnowledgeGraph:
    graph = KnowledgeGraph()
    graph.add_entity(Entity(id="e1", name="人工智能", type="技术"))
    graph.add_entity(Entity(id="e2", name="机器学习", type="技术"))
    graph.add_relationship(Relationship(id="r1", source_id="e1", target_id="e2", type="包含"))
    return graph


@pytest.mark.unit
class TestAnalysisWorkflowService:
    """Project analysis workflows into delivery-friendly payloads."""

    def test_graph_analyze_uses_default_graph_components(self, sample_article) -> None:
        fetch_use_case = Mock()
        fetch_use_case.execute.return_value = sample_article

        extractor = Mock()
        extractor.extract.return_value = ExtractionResult(
            entities=[Entity(id="e1", name="人工智能", type="技术")],
            relationships=[Relationship(id="r1", source_id="e1", target_id="e1", type="相关")],
        )
        graph = _sample_graph()
        builder = Mock()
        builder.build.return_value = graph
        detector = Mock()
        detector.detect.return_value = [
            Community(id="c1", level=0, entity_ids=["e1", "e2"], title="技术社区")
        ]

        service = AnalysisWorkflowService(
            fetch_use_case=fetch_use_case,
            summarize_use_case=Mock(),
            entity_extractor=extractor,
            graph_builder=builder,
            community_detector=detector,
        )

        payload = service.graph_analyze(str(sample_article.url))

        assert payload.title == sample_article.title
        assert payload.graph_stats.entity_count == 2
        assert payload.graph_stats.relationship_count == 1
        assert payload.graph_stats.community_count == 1
        assert payload.relationships[0].source == "人工智能"
        assert payload.relationships[0].target == "机器学习"
        extractor.extract.assert_called_once_with(sample_article.content_text)
        builder.build.assert_called_once()
        detector.detect.assert_called_once_with(graph)

    def test_graph_analyze_prefers_graphrag_when_available(
        self,
        sample_article,
        sample_summary,
    ) -> None:
        fetch_use_case = Mock()
        fetch_use_case.execute.return_value = sample_article

        graph = _sample_graph()
        graphrag = Mock()
        graphrag.summarize.return_value = sample_summary
        graphrag.get_knowledge_graph.return_value = graph

        extractor = Mock()
        service = AnalysisWorkflowService(
            fetch_use_case=fetch_use_case,
            summarize_use_case=Mock(),
            entity_extractor=extractor,
            graph_builder=Mock(),
            community_detector=Mock(),
            summarizers={"graphrag-simple": graphrag},
        )

        payload = service.graph_analyze(str(sample_article.url))

        assert payload.graph_stats.entity_count == 2
        graphrag.summarize.assert_called_once()
        content_arg = graphrag.summarize.call_args.args[0]
        assert isinstance(content_arg, ArticleContent)
        assert content_arg.text == sample_article.content_text
        extractor.extract.assert_not_called()

    def test_compare_articles_projects_common_entities_and_tags(
        self,
        sample_article,
        sample_summary,
    ) -> None:
        second_article = sample_article
        fetch_use_case = Mock()
        fetch_use_case.execute.side_effect = [sample_article, second_article]

        extractor = Mock()
        extractor.extract.return_value = ExtractionResult(
            entities=[
                Entity(id="e1", name="AI", type="技术"),
                Entity(id="e2", name="Python", type="技术"),
            ],
            relationships=[],
        )
        summarize_use_case = Mock()
        summarize_use_case.execute.return_value = sample_summary

        service = AnalysisWorkflowService(
            fetch_use_case=fetch_use_case,
            summarize_use_case=summarize_use_case,
            entity_extractor=extractor,
            graph_builder=Mock(),
            community_detector=Mock(),
        )

        payload = service.compare_articles(
            ["https://example.com/a", "https://example.com/b"],
            aspects=["entities"],
        )

        assert payload.article_count == 2
        assert payload.comparison.common_entities == ("AI", "Python")
        assert payload.comparison.common_tags == tuple(sorted(sample_summary.tags))
        assert payload.comparison.total_word_count == sample_article.word_count * 2
        assert payload.articles[0].summary == sample_summary.content

    def test_compare_articles_requires_at_least_two_urls(self) -> None:
        service = AnalysisWorkflowService(
            fetch_use_case=Mock(),
            summarize_use_case=Mock(),
            entity_extractor=Mock(),
            graph_builder=Mock(),
            community_detector=Mock(),
        )

        with pytest.raises(ValueError, match="至少需要 2 篇文章"):
            service.compare_articles(["https://example.com/a"])

    def test_track_topic_sorts_matches_and_isolates_failures(self, sample_article) -> None:
        first_content = "AI 是主题。\n这是一段足够长的 AI 相关内容，用于生成摘录。AI 再次出现。"
        sample_article.update_content(ArticleContent.from_text(first_content))

        fetch_use_case = Mock()
        fetch_use_case.execute.side_effect = [sample_article, RuntimeError("boom")]

        service = AnalysisWorkflowService(
            fetch_use_case=fetch_use_case,
            summarize_use_case=Mock(),
            entity_extractor=Mock(),
            graph_builder=Mock(),
            community_detector=Mock(),
        )

        payload = service.track_topic(["https://example.com/a", "https://example.com/b"], "AI")

        assert payload.total_articles == 2
        assert payload.articles_with_topic == 1
        assert payload.total_occurrences == 3
        assert len(payload.results) == 1
        assert payload.results[0].topic_occurrences == 3
        assert payload.results[0].relevant_excerpts

    def test_evaluate_summary_uses_generated_summary_when_missing(
        self,
        sample_article,
        sample_summary,
    ) -> None:
        sample_article.update_content(
            ArticleContent.from_text(
                "人工智能人工智能人工智能正在改变生活。机器学习是人工智能的重要技术。"
            )
        )
        fetch_use_case = Mock()
        fetch_use_case.execute.return_value = sample_article
        summarize_use_case = Mock()
        summarize_use_case.execute.return_value = sample_summary

        service = AnalysisWorkflowService(
            fetch_use_case=fetch_use_case,
            summarize_use_case=summarize_use_case,
            entity_extractor=Mock(),
            graph_builder=Mock(),
            community_detector=Mock(),
        )

        payload = service.evaluate_summary(str(sample_article.url), method="simple")

        assert payload.title == sample_article.title
        assert payload.summary == sample_summary.content
        assert payload.original_length == len(sample_article.content_text)
        assert 0 <= payload.evaluation.overall_score <= 1
        summarize_use_case.execute.assert_called_once_with(
            sample_article,
            method="simple",
            max_length=500,
        )
