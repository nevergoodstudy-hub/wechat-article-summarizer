"""Mapping helpers for single-article display models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .single_process_models import ArticleDisplayModel, SummaryDisplayModel

if TYPE_CHECKING:
    from ....domain.entities import Article, Summary


def convert_article(article: Article) -> ArticleDisplayModel:
    """Convert a domain article into a GUI display model."""
    publish_time = ""
    if article.publish_time:
        publish_time = article.publish_time.strftime("%Y-%m-%d %H:%M")

    content_preview = ""
    if article.content:
        text = article.content_text or ""
        content_preview = text[:500] + "..." if len(text) > 500 else text

    return ArticleDisplayModel(
        url=str(article.url),
        title=article.title,
        author=article.author or "",
        account_name=article.account_name or "",
        publish_time=publish_time,
        content_preview=content_preview,
        word_count=len(article.content_text or "") if article.content else 0,
    )


def convert_summary(summary: Summary) -> SummaryDisplayModel:
    """Convert a domain summary into a GUI display model."""
    generated_at = ""
    if summary.created_at:
        generated_at = summary.created_at.strftime("%Y-%m-%d %H:%M:%S")

    return SummaryDisplayModel(
        content=summary.content,
        key_points=list(summary.key_points) if summary.key_points else [],
        tags=list(summary.tags) if summary.tags else [],
        method=summary.method.value if summary.method else "",
        model_name=summary.model_name or "",
        generated_at=generated_at,
    )


__all__ = ["convert_article", "convert_summary"]
