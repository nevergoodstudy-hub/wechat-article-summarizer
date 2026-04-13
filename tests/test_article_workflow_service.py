"""Tests for the article workflow vertical slice."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from wechat_summarizer.domain.value_objects import ArticleContent
from wechat_summarizer.features.article_workflow import ArticleWorkflowService


@pytest.mark.unit
class TestArticleWorkflowService:
    """Project delivery-friendly orchestration tests."""

    def test_fetch_truncates_content(
        self,
        sample_article,
        mock_summarizer: Mock,
    ) -> None:
        long_text = "A" * 128
        sample_article.update_content(ArticleContent.from_text(long_text))

        fetch_use_case = Mock()
        fetch_use_case.execute.return_value = sample_article
        summarize_use_case = Mock()

        service = ArticleWorkflowService(fetch_use_case, summarize_use_case)

        payload = service.fetch(str(sample_article.url), content_limit=32)

        assert payload.title == sample_article.title
        assert payload.word_count == len(long_text)
        assert payload.content == long_text[:32]
        assert payload.content_truncated is True
        fetch_use_case.execute.assert_called_once_with(str(sample_article.url))

    def test_get_info_builds_preview(
        self,
        sample_article,
    ) -> None:
        long_text = "B" * 80
        sample_article.update_content(ArticleContent.from_text(long_text))

        fetch_use_case = Mock()
        fetch_use_case.execute.return_value = sample_article

        service = ArticleWorkflowService(fetch_use_case, Mock())
        payload = service.get_info(str(sample_article.url), preview_limit=20)

        assert payload.preview == f"{long_text[:20]}..."
        assert payload.publish_time == sample_article.publish_time_str

    def test_summarize_projects_nested_payloads(
        self,
        sample_article,
        sample_summary,
    ) -> None:
        fetch_use_case = Mock()
        fetch_use_case.execute.return_value = sample_article
        summarize_use_case = Mock()
        summarize_use_case.execute.return_value = sample_summary

        service = ArticleWorkflowService(fetch_use_case, summarize_use_case)
        payload = service.summarize(str(sample_article.url), method="simple", max_length=120)

        assert payload.article.title == sample_article.title
        assert payload.summary.content == sample_summary.content
        assert payload.summary.key_points == sample_summary.key_points
        assert payload.summary.tags == sample_summary.tags
        summarize_use_case.execute.assert_called_once_with(
            sample_article,
            method="simple",
            max_length=120,
        )

    def test_batch_summarize_isolates_per_item_failures(
        self,
        sample_article,
        sample_summary,
    ) -> None:
        fetch_use_case = Mock()
        fetch_use_case.execute.side_effect = [sample_article, sample_article]
        summarize_use_case = Mock()
        summarize_use_case.execute.side_effect = [sample_summary, RuntimeError("boom")]

        service = ArticleWorkflowService(fetch_use_case, summarize_use_case)
        payload = service.batch_summarize(
            ["https://example.com/a", "https://example.com/b"],
            method="simple",
            max_length=80,
        )

        assert payload.total == 2
        assert payload.processed == 2
        assert payload.results[0].success is True
        assert payload.results[0].summary == sample_summary.content
        assert payload.results[1].success is False
        assert payload.results[1].error == "boom"

    def test_list_available_methods_delegates_to_use_case(self) -> None:
        summarize_use_case = Mock()
        summarize_use_case.list_available_methods.return_value = ("simple", "openai")

        service = ArticleWorkflowService(Mock(), summarize_use_case)

        assert service.list_available_methods() == ["simple", "openai"]
