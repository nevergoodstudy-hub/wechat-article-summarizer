"""导出器基类"""

from abc import ABC, abstractmethod

from ....domain.entities import Article


class BaseExporter(ABC):
    """导出器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """导出器名称"""
        pass

    @property
    @abstractmethod
    def target(self) -> str:
        """导出目标标识"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass

    @abstractmethod
    def export(
        self,
        article: Article,
        path: str | None = None,
        **options,
    ) -> str:
        """导出文章"""
        pass
