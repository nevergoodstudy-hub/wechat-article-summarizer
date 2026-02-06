"""领域事件

目前事件仅用于日志 / 追踪；尚未接入事件总线或发布-订阅机制。
如需扩展为真正的 Event Sourcing / CQRS，应在此模块引入 EventBus 抽象。
"""

from .article_events import (
    ArticleExported,
    ArticleFetched,
    ArticleSummarized,
    BatchProcessCompleted,
    BatchProcessStarted,
    DomainEvent,
)

__all__ = [
    "DomainEvent",
    "ArticleFetched",
    "ArticleSummarized",
    "ArticleExported",
    "BatchProcessStarted",
    "BatchProcessCompleted",
]
