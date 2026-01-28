"""摘要器基类"""

from abc import ABC, abstractmethod

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent


class BaseSummarizer(ABC):
    """摘要器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """摘要器名称"""
        pass

    @property
    @abstractmethod
    def method(self) -> SummaryMethod:
        """摘要方法"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass

    @abstractmethod
    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """生成摘要"""
        pass
