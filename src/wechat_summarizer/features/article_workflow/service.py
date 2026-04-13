"""Feature service for fetch/summarize article workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .dto import (
    ArticleFetchPayload,
    ArticleInfoPayload,
    ArticleMetadataPayload,
    ArticleSummaryPayload,
    BatchSummaryItemPayload,
    BatchSummaryPayload,
    SummaryPayload,
)

if TYPE_CHECKING:
    from ...application.use_cases.export_article import ExportArticleUseCase
    from ...application.use_cases.fetch_article import FetchArticleUseCase
    from ...application.use_cases.summarize_article import SummarizeArticleUseCase
    from ...domain.entities import Article, Summary


class ArticleWorkflowService:
    """Application-facing workflow service for article operations."""

    def __init__(
        self,
        fetch_use_case: FetchArticleUseCase,
        summarize_use_case: SummarizeArticleUseCase,
        export_use_case: ExportArticleUseCase | None = None,
    ) -> None:
        self._fetch_use_case = fetch_use_case
        self._summarize_use_case = summarize_use_case
        self._export_use_case = export_use_case

    def fetch(self, url: str, content_limit: int | None = 10_000) -> ArticleFetchPayload:
        """Fetch an article and project it into a delivery-friendly payload."""
        article = self._fetch_use_case.execute(url)
        content = article.content_text
        content_truncated = False

        if content_limit is not None and len(content) > content_limit:
            content = content[:content_limit]
            content_truncated = True

        metadata = self._to_metadata(article)
        return ArticleFetchPayload(
            **metadata.__dict__,
            content=content,
            content_truncated=content_truncated,
        )

    def get_info(self, url: str, preview_limit: int = 500) -> ArticleInfoPayload:
        """Fetch article info and build a short preview."""
        article = self._fetch_use_case.execute(url)
        preview = article.content_text[:preview_limit]
        if len(article.content_text) > preview_limit:
            preview += "..."

        metadata = self._to_metadata(article)
        return ArticleInfoPayload(**metadata.__dict__, preview=preview)

    def summarize(
        self,
        url: str,
        method: str = "simple",
        max_length: int = 500,
    ) -> ArticleSummaryPayload:
        """Fetch an article and summarize it through the existing use case."""
        article = self._fetch_use_case.execute(url)
        summary = self._summarize_use_case.execute(
            article,
            method=method,
            max_length=max_length,
        )
        article.attach_summary(summary)

        return ArticleSummaryPayload(
            article=self._to_metadata(article),
            summary=self._to_summary(summary),
        )

    def batch_summarize(
        self,
        urls: list[str],
        method: str = "simple",
        max_length: int = 300,
    ) -> BatchSummaryPayload:
        """Batch summarize multiple articles while isolating per-item failures."""
        results: list[BatchSummaryItemPayload] = []

        for url in urls:
            try:
                summary_payload = self.summarize(url, method=method, max_length=max_length)
                results.append(
                    BatchSummaryItemPayload(
                        url=url,
                        success=True,
                        title=summary_payload.article.title,
                        summary=summary_payload.summary.content,
                        tags=summary_payload.summary.tags,
                    )
                )
            except Exception as exc:
                results.append(
                    BatchSummaryItemPayload(
                        url=url,
                        success=False,
                        error=str(exc),
                    )
                )

        return BatchSummaryPayload(
            total=len(urls),
            processed=len(results),
            results=tuple(results),
        )

    def list_available_methods(self) -> list[str]:
        """List available summarization methods via the existing use case."""
        return list(self._summarize_use_case.list_available_methods())

    def export_available(self) -> bool:
        """Return whether the workflow currently has export orchestration available."""
        return self._export_use_case is not None

    @staticmethod
    def _to_metadata(article: Article) -> ArticleMetadataPayload:
        return ArticleMetadataPayload(
            url=str(article.url),
            title=article.title,
            author=article.author,
            account_name=article.account_name,
            publish_time=article.publish_time_str,
            word_count=article.word_count,
        )

    @staticmethod
    def _to_summary(summary: Summary) -> SummaryPayload:
        return SummaryPayload(
            content=summary.content,
            key_points=summary.key_points,
            tags=summary.tags,
            method=summary.method.value,
            model_name=summary.model_name,
        )
