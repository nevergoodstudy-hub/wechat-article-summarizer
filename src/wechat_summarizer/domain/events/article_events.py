"""文章领域事件"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class DomainEvent:
    """领域事件基类"""

    # 注意：该字段有默认值；为避免子类新增非默认字段时触发 dataclass 参数顺序限制，
    # 将其设为 init=False（由 default_factory 自动填充）。
    occurred_at: datetime = field(default_factory=datetime.now, init=False)


@dataclass(frozen=True)
class ArticleFetched(DomainEvent):
    """文章抓取完成事件"""

    article_id: UUID
    url: str
    title: str
    word_count: int


@dataclass(frozen=True)
class ArticleSummarized(DomainEvent):
    """文章摘要生成完成事件"""

    article_id: UUID
    method: str
    tokens_used: int


@dataclass(frozen=True)
class ArticleExported(DomainEvent):
    """文章导出完成事件"""

    article_id: UUID
    target: str  # onenote, notion, obsidian, file
    path: str | None = None


@dataclass(frozen=True)
class BatchProcessStarted(DomainEvent):
    """批量处理开始事件"""

    batch_id: UUID
    total_count: int


@dataclass(frozen=True)
class BatchProcessCompleted(DomainEvent):
    """批量处理完成事件"""

    batch_id: UUID
    success_count: int
    failed_count: int
