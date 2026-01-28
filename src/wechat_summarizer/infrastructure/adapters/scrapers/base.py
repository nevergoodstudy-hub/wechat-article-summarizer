"""抓取器基类"""

from abc import ABC, abstractmethod

from ....domain.entities import Article
from ....domain.value_objects import ArticleURL


class BaseScraper(ABC):
    """抓取器抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """抓取器名称"""
        pass

    @abstractmethod
    def can_handle(self, url: ArticleURL) -> bool:
        """判断是否能处理该URL"""
        pass

    @abstractmethod
    def scrape(self, url: ArticleURL) -> Article:
        """抓取文章"""
        pass
