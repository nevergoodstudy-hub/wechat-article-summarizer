"""Async batch process use case tests."""

from __future__ import annotations

import asyncio
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


class _ConcurrencyTrackingScraper:
    """Async scraper double that records concurrent calls."""

    name = "tracking-async-scraper"

    def __init__(self) -> None:
        self.running = 0
        self.max_seen = 0
        self._lock = asyncio.Lock()

    def can_handle(self, url: ArticleURL) -> bool:
        return True

    async def scrape_async(self, url: ArticleURL) -> Article:
        async with self._lock:
            self.running += 1
            self.max_seen = max(self.max_seen, self.running)

        await asyncio.sleep(0.01)

        async with self._lock:
            self.running -= 1

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
    assert result.performance_sample is not None
    assert result.performance_sample.name == "async_batch_process_urls"
    assert result.performance_sample.duration_ms >= 0
    assert result.performance_sample.peak_memory_kb >= 0
    assert result.performance_sample.metadata["url_count"] == 2
    assert result.performance_sample.metadata["success_count"] == 1
    assert result.performance_sample.metadata["failed_count"] == 1
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


@pytest.mark.unit
async def test_async_batch_respects_max_concurrent_limit() -> None:
    """Batch processing should use the configured concurrency cap."""
    scraper = _ConcurrencyTrackingScraper()
    use_case = AsyncBatchProcessUseCase(
        scrapers=[scraper],
        max_concurrent=2,
    )

    result = await use_case.process_urls(
        [f"https://example.com/{index}" for index in range(6)],
        summarize=False,
    )

    assert result.success_count == 6
    assert scraper.max_seen <= 2
