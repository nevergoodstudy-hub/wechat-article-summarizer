"""Async batch process use case tests."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from wechat_summarizer.application.use_cases.async_batch_process import (
    AsyncBatchProcessUseCase,
)
from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL


@dataclass
class _AsyncScraper:
    """Tiny async scraper double for batch tests."""

    failures: set[str]
    name: str = "fake-async-scraper"

    def can_handle(self, url: ArticleURL) -> bool:
        return True

    async def scrape_async(self, url: ArticleURL) -> Article:
        if str(url) in self.failures:
            raise RuntimeError("boom")
        return Article(
            url=url,
            title=f"Article {url.domain}",
            content=ArticleContent.from_text("hello async batch"),
        )


@pytest.mark.unit
async def test_async_batch_result_includes_per_url_failures() -> None:
    """Failed URLs should be visible to callers, not only progress callbacks."""
    failing_url = "https://example.com/fail"
    use_case = AsyncBatchProcessUseCase(
        scrapers=[_AsyncScraper(failures={failing_url})],
        max_concurrent=2,
    )

    result = await use_case.process_urls(
        [
            "https://example.com/ok",
            failing_url,
        ],
        summarize=False,
    )

    assert result.success_count == 1
    assert result.failed_count == 1
    assert result.total == 2
    assert result.errors == [(failing_url, "没有可用的抓取器能处理URL: https://example.com/fail")]


@pytest.mark.unit
async def test_async_batch_progress_and_result_failures_match() -> None:
    """Progress and final result should expose the same failed URL details."""
    failing_url = "https://example.com/fail"
    progress_errors: list[list[tuple[str, str]]] = []
    use_case = AsyncBatchProcessUseCase(
        scrapers=[_AsyncScraper(failures={failing_url})],
        max_concurrent=1,
    )

    result = await use_case.process_urls(
        [failing_url],
        summarize=False,
        on_progress=lambda progress: progress_errors.append(list(progress.errors)),
    )

    assert progress_errors[-1] == result.errors
