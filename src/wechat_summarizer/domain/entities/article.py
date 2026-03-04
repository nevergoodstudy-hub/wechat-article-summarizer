"""文章聚合根实体 - DDD核心"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from ...shared.utils import utc_now

if TYPE_CHECKING:
    from ..value_objects import ArticleContent, ArticleURL
    from .source import ArticleSource
    from .summary import Summary


@dataclass(frozen=True)
class Article:
    """
    文章聚合根 (不可变实体)

    聚合根是DDD中的核心概念，它是一个实体的边界，
    所有对聚合内部对象的访问都必须通过聚合根进行。

    设计为 frozen=True 以确保实体不可变性。
    受控变异通过 object.__setattr__ 在聚合根方法内完成。
    """

    # 核心属性（url 必填）
    url: ArticleURL
    title: str = ""

    # 身份标识
    id: UUID = field(default_factory=uuid4)
    author: str | None = None
    account_name: str | None = None
    publish_time: datetime | None = None

    # 内容
    content: ArticleContent | None = None

    # 来源信息
    source: ArticleSource | None = None

    # 元数据
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    # 摘要 (可选，处理后添加)
    summary: Summary | None = None

    @property
    def content_text(self) -> str:
        """获取纯文本内容"""
        if self.content is None:
            return ""
        return self.content.text

    @property
    def content_html(self) -> str:
        """获取HTML内容"""
        if self.content is None:
            return ""
        return self.content.html

    @property
    def word_count(self) -> int:
        """计算字数"""
        return len(self.content_text)

    @property
    def publish_time_str(self) -> str:
        """格式化发布时间"""
        if self.publish_time is None:
            return "未知"
        return self.publish_time.strftime("%Y-%m-%d %H:%M:%S")

    def attach_summary(self, summary: Summary) -> None:
        """附加摘要到文章（受控变异）"""
        object.__setattr__(self, "summary", summary)
        object.__setattr__(self, "updated_at", utc_now())

    def update_content(self, content: ArticleContent) -> None:
        """更新文章内容（受控变异）"""
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "updated_at", utc_now())
