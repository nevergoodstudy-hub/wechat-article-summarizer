"""Display models for the single-article ViewModel."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ArticleDisplayModel:
    """Article data prepared for GUI display."""

    url: str = ""
    title: str = ""
    author: str = ""
    account_name: str = ""
    publish_time: str = ""
    content_preview: str = ""
    word_count: int = 0


@dataclass
class SummaryDisplayModel:
    """Summary data prepared for GUI display."""

    content: str = ""
    key_points: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    method: str = ""
    model_name: str = ""
    generated_at: str = ""


__all__ = ["ArticleDisplayModel", "SummaryDisplayModel"]
