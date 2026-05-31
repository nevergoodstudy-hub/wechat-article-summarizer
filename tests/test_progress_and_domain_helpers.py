"""Focused tests for pure helpers and domain services."""

from __future__ import annotations

import pytest

from wechat_summarizer.domain.entities import Article, Summary
from wechat_summarizer.domain.exceptions import (
    ArticleNotFoundError,
    DomainError,
    InvalidContentError,
    InvalidURLError,
)
from wechat_summarizer.domain.services.article_processor import ArticleProcessorService
from wechat_summarizer.domain.services.quality_evaluator import (
    QualityScore,
    SummaryQualityEvaluator,
)
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.shared.progress import (
    BatchProgressTracker,
    ProgressInfo,
    ProgressTracker,
    format_duration,
)
from wechat_summarizer.shared.utils.text import (
    chunk_text,
    clean_whitespace,
    count_words,
    extract_numbers,
    normalize_url,
    remove_html_tags,
    truncate_text,
)


class TestTextHelpers:
    """Text helper regression tests."""

    def test_truncate_text_preserves_short_text(self) -> None:
        assert truncate_text("short", max_length=10) == "short"

    def test_truncate_text_adds_suffix(self) -> None:
        assert truncate_text("abcdefghij", max_length=6, suffix="..") == "abcd.."

    def test_clean_whitespace_collapses_spaces_and_blank_lines(self) -> None:
        assert clean_whitespace("  a\t\tb\n\n\n\nc  ") == "a b\n\nc"

    def test_chunk_text_short_text_yields_once(self) -> None:
        assert list(chunk_text("abc", chunk_size=10, overlap=2)) == ["abc"]

    def test_chunk_text_uses_overlap_and_paragraph_boundary(self) -> None:
        chunks = list(chunk_text("aaaa\nbbbb\ncccc\ndddd", chunk_size=10, overlap=2))

        assert chunks[0].endswith("\n")
        assert len(chunks) > 1
        assert "".join(chunks).startswith("aaaa\nbbbb")

    def test_extract_numbers_supports_signed_decimals(self) -> None:
        assert extract_numbers("a -1.5 b +2 c 3") == [-1.5, 2.0, 3.0]

    def test_count_words_mixed_chinese_and_english(self) -> None:
        assert count_words("AI 正在改变 world") == 6

    def test_remove_html_tags(self) -> None:
        assert remove_html_tags("<p>Hello <strong>world</strong></p>") == "Hello world"

    def test_normalize_url_adds_scheme_and_strips_slash(self) -> None:
        assert normalize_url(" example.com/path/ ") == "https://example.com/path"


class TestProgressHelpers:
    """Progress tracker behavior."""

    def test_format_duration_boundaries(self) -> None:
        assert format_duration(-1) == "--:--"
        assert format_duration(float("inf")) == "--:--"
        assert format_duration(9.9) == "00:09"
        assert format_duration(61) == "01:01"
        assert format_duration(3661) == "01:01:01"

    def test_progress_info_formatting(self) -> None:
        info = ProgressInfo(
            current=3,
            total=10,
            percentage=30.0,
            elapsed_seconds=65,
            eta_seconds=125,
            rate=0.5,
            current_item="article",
        )

        assert info.elapsed_formatted == "01:05"
        assert info.eta_formatted == "02:05"
        assert info.rate_formatted == "0.50 篇/秒"
        assert info.progress_text == "3/10"
        assert info.percentage_text == "30.0%"
        assert "[article]" in info.to_log_string()

    def test_progress_info_low_rate_and_finished_eta(self) -> None:
        assert ProgressInfo(rate=0.001).rate_formatted == "计算中..."
        assert ProgressInfo(rate=2).rate_formatted == "2.0 篇/秒"
        assert ProgressInfo(eta_seconds=0).eta_formatted == "--:--"

    def test_progress_tracker_update_finish_and_reset(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        times = iter([100.0, 101.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0])
        monkeypatch.setattr("wechat_summarizer.shared.progress.time.time", lambda: next(times))
        callback_items: list[ProgressInfo] = []
        tracker = ProgressTracker(total=3, callback=callback_items.append, log_interval=10)

        first = tracker.update(current_item="one")
        second = tracker.update(increment=2, current_item="two")
        finished = tracker.finish()

        assert first.current == 1
        assert second.current == 3
        assert tracker.is_complete is True
        assert finished.current == 3
        assert len(callback_items) == 2

        tracker.reset(total=2)
        assert tracker.total == 2
        assert tracker.current == 0
        assert tracker.is_complete is False

    def test_progress_tracker_callback_errors_are_ignored(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        times = iter([200.0, 201.0, 202.0])
        monkeypatch.setattr("wechat_summarizer.shared.progress.time.time", lambda: next(times))

        def failing_callback(_info: ProgressInfo) -> None:
            raise RuntimeError("boom")

        tracker = ProgressTracker(total=1, callback=failing_callback)

        info = tracker.update()

        assert info.current == 1

    def test_batch_progress_tracker_counts_failures_and_reset(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        times = iter([300.0, 301.0, 302.0, 303.0, 304.0, 305.0, 306.0])
        monkeypatch.setattr("wechat_summarizer.shared.progress.time.time", lambda: next(times))
        tracker = BatchProgressTracker(total=2)

        tracker.update_success("ok")
        tracker.update_failure("bad", error="network")

        assert tracker.success_count == 1
        assert tracker.failure_count == 1
        assert tracker.failures == [("bad", "network")]
        assert "成功: 1" in tracker.get_summary()

        tracker.reset(total=3)
        assert tracker.success_count == 0
        assert tracker.failure_count == 0
        assert tracker.failures == []


class TestDomainExceptions:
    """Domain-owned exception compatibility."""

    def test_domain_exception_payload(self) -> None:
        err = InvalidURLError("bad url", details={"field": "url"}, cause=ValueError("x"))

        assert isinstance(err, DomainError)
        assert err.code == 1002
        assert err.user_message == "bad url"
        assert err.details == {"field": "url"}
        assert isinstance(err.cause, ValueError)
        assert err.to_dict() == {
            "error_code": 1002,
            "error_type": "INVALID_URL",
            "message": "bad url",
            "details": {"field": "url"},
        }
        assert "bad url" in repr(err)

    def test_specific_domain_error_defaults(self) -> None:
        assert InvalidContentError().user_message == "无效的内容"
        assert ArticleNotFoundError().code == 2004


class TestArticleProcessorService:
    """ArticleProcessorService tests."""

    @pytest.fixture
    def service(self) -> ArticleProcessorService:
        return ArticleProcessorService()

    @pytest.fixture
    def article(self) -> Article:
        return Article(
            url=ArticleURL.from_string("https://mp.weixin.qq.com/s/test"),
            content=ArticleContent.from_text("人工智能" * 50),
        )

    def test_process_article_attaches_summary(
        self,
        service: ArticleProcessorService,
        article: Article,
    ) -> None:
        summary = Summary(content="summary")

        result = service.process_article(article, summary)

        assert result is article
        assert article.summary == summary

    def test_process_article_without_summary_returns_article(
        self,
        service: ArticleProcessorService,
        article: Article,
    ) -> None:
        assert service.process_article(article) is article

    def test_validate_content_requires_text_and_minimum_length(
        self,
        service: ArticleProcessorService,
    ) -> None:
        assert service.validate_content(ArticleContent()) is False
        assert service.validate_content(ArticleContent.from_text("短文")) is False
        assert service.validate_content(ArticleContent.from_text("内容" * 60)) is True

    def test_estimate_tokens_and_chunk_decision(self, service: ArticleProcessorService) -> None:
        content = ArticleContent.from_text("中文" * 300 + "abcd" * 100)

        estimated = service.estimate_tokens(content)

        assert estimated > 0
        assert service.should_chunk(content, max_tokens=1) is True
        assert service.should_chunk(content, max_tokens=estimated + 1) is False


class TestSummaryQualityEvaluator:
    """Heuristic summary quality evaluator tests."""

    @pytest.fixture
    def evaluator(self) -> SummaryQualityEvaluator:
        return SummaryQualityEvaluator()

    def test_quality_score_to_dict(self) -> None:
        score = QualityScore(completeness=0.1, conciseness=0.2, coherence=0.3, overall=0.2)

        assert score.to_dict() == {
            "completeness": 0.1,
            "conciseness": 0.2,
            "coherence": 0.3,
            "overall": 0.2,
        }

    def test_evaluate_returns_average_score(self, evaluator: SummaryQualityEvaluator) -> None:
        article = Article(
            url=ArticleURL.from_string("https://mp.weixin.qq.com/s/test"),
            content=ArticleContent.from_text("人工智能 技术 创新 发展 " * 20),
        )
        summary = Summary(content="人工智能 技术 创新。")

        score = evaluator.evaluate(article, summary)

        assert 0.0 <= score.completeness <= 1.0
        assert 0.0 <= score.conciseness <= 1.0
        assert 0.0 <= score.coherence <= 1.0
        assert score.overall == pytest.approx(
            (score.completeness + score.conciseness + score.coherence) / 3
        )

    def test_completeness_empty_and_keyword_cases(
        self,
        evaluator: SummaryQualityEvaluator,
    ) -> None:
        assert evaluator._evaluate_completeness("", "summary") == 0.0
        assert evaluator._evaluate_completeness("的 是 在", "summary") == 1.0
        assert evaluator._evaluate_completeness("alpha beta gamma", "alpha") > 0

    @pytest.mark.parametrize(
        ("original", "summary", "expected"),
        [
            ("", "anything", 1.0),
            ("1234567890", "", 0.0),
            ("x" * 1000, "x" * 20, 0.5),
            ("x" * 1000, "x" * 100, 1.0),
            ("x" * 1000, "x" * 300, 0.7),
            ("x" * 1000, "x" * 500, 0.3),
        ],
    )
    def test_conciseness_branches(
        self,
        evaluator: SummaryQualityEvaluator,
        original: str,
        summary: str,
        expected: float,
    ) -> None:
        assert evaluator._evaluate_conciseness(original, summary) == expected

    @pytest.mark.parametrize(
        ("summary", "expected"),
        [
            ("", 0.0),
            ("fragment without chinese period", 1.0),
            ("这是一个长度适中的完整句子。", 1.0),
            ("短。", 0.4),
            ("x" * 120 + "。", 0.7),
            ("x" * 200 + "。", 0.4),
        ],
    )
    def test_coherence_branches(
        self,
        evaluator: SummaryQualityEvaluator,
        summary: str,
        expected: float,
    ) -> None:
        assert evaluator._evaluate_coherence(summary) == expected

    def test_extract_keywords_filters_stopwords_and_limits(
        self,
        evaluator: SummaryQualityEvaluator,
    ) -> None:
        keywords = evaluator._extract_keywords("人工智能 人工智能 技术 and the innovation")

        assert keywords[0] == "人工智能"
        assert "and" not in keywords
        assert "the" not in keywords
