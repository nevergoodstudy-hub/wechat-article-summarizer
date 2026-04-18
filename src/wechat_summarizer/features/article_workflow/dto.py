"""DTOs for the article workflow vertical slice."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArticleMetadataPayload:
    """Common article metadata exposed to delivery layers."""

    url: str
    title: str
    author: str | None
    account_name: str | None
    publish_time: str
    word_count: int


@dataclass(frozen=True)
class ArticleFetchPayload(ArticleMetadataPayload):
    """Fetched article content prepared for delivery layers."""

    content: str
    content_truncated: bool


@dataclass(frozen=True)
class ArticleInfoPayload(ArticleMetadataPayload):
    """Lightweight article information prepared for previews."""

    preview: str


@dataclass(frozen=True)
class SummaryPayload:
    """Summary data prepared for delivery layers."""

    content: str
    key_points: tuple[str, ...]
    tags: tuple[str, ...]
    method: str
    model_name: str | None


@dataclass(frozen=True)
class ArticleSummaryPayload:
    """Article metadata plus summary data."""

    article: ArticleMetadataPayload
    summary: SummaryPayload


@dataclass(frozen=True)
class BatchSummaryItemPayload:
    """Single item in a batch summarize response."""

    url: str
    success: bool
    title: str | None = None
    summary: str | None = None
    tags: tuple[str, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class BatchSummaryPayload:
    """Batch summarize response."""

    total: int
    processed: int
    results: tuple[BatchSummaryItemPayload, ...]
