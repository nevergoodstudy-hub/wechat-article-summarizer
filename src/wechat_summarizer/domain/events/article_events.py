"""文章领域事件

注意：这些事件目前仅作为数据结构定义，尚未接入事件总线。
项目中暂无发布/订阅机制，事件未在 use case 中实际发布。
如需启用事件驱动，需实现 EventBus 并在 use case 中发布事件。

TODO: 实现 EventBus 抽象并在 FetchArticleUseCase / SummarizeArticleUseCase 中发布事件。
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from ...shared.utils import utc_now


@dataclass(frozen=True)
class DomainEvent:
    """领域事件基类"""

    # 注意：该字段有默认值；为避免子类新增非默认字段时触发 dataclass 参数顺序限制，
    # 将其设为 init=False（由 default_factory 自动填充）。
    occurred_at: datetime = field(default_factory=utc_now, init=False)


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
