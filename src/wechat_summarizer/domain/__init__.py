"""
领域层 - DDD核心

领域层包含：
- entities: 领域实体（聚合根、实体）
- value_objects: 值对象
- services: 领域服务
- events: 领域事件

依赖规则：领域层不依赖任何外部层
"""

from .entities import Article, ArticleSource, SourceType, Summary, SummaryMethod, SummaryStyle
from .services import ArticleProcessorService
from .value_objects import ArticleContent, ArticleURL

__all__ = [
    # Entities
    "Article",
    "Summary",
    "ArticleSource",
    "SourceType",
    "SummaryMethod",
    "SummaryStyle",
    # Value Objects
    "ArticleURL",
    "ArticleContent",
    # Services
    "ArticleProcessorService",
]
