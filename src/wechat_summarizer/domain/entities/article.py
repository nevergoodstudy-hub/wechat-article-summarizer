"""文章聚合根实体 - DDD核心"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from ..value_objects import ArticleContent, ArticleURL
    from .source import ArticleSource


@dataclass
class Article:
    """
    文章聚合根

    聚合根是DDD中的核心概念，它是一个实体的边界，
    所有对聚合内部对象的访问都必须通过聚合根进行。
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
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

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
        """附加摘要到文章"""
        self.summary = summary
        self.updated_at = datetime.now()

    def update_content(self, content: ArticleContent) -> None:
        """更新文章内容"""
        self.content = content
        self.updated_at = datetime.now()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Article):
            return False
        return self.id == other.id


# 避免循环导入
from .summary import Summary  # noqa: E402
