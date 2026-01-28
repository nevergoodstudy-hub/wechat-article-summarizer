"""抓取器出站端口 - 定义抓取器适配器必须实现的接口"""

from typing import Protocol, runtime_checkable

from ....domain.entities import Article
from ....domain.value_objects import ArticleURL


@runtime_checkable
class ScraperPort(Protocol):
    """
    抓取器端口

    定义抓取器适配器必须实现的接口。
    基础设施层的具体抓取器实现此接口。
    """

    @property
    def name(self) -> str:
        """抓取器名称"""
        ...

    def can_handle(self, url: ArticleURL) -> bool:
        """
        判断是否能处理该URL

        Args:
            url: 文章URL

        Returns:
            是否能处理
        """
        ...

    def scrape(self, url: ArticleURL) -> Article:
        """
        抓取文章

        Args:
            url: 文章URL

        Returns:
            抓取到的文章实体

        Raises:
            ScraperError: 抓取失败
        """
        ...


class AsyncScraperPort(Protocol):
    """
    异步抓取器端口

    支持异步操作的抓取器接口。
    """

    @property
    def name(self) -> str:
        """抓取器名称"""
        ...

    def can_handle(self, url: ArticleURL) -> bool:
        """判断是否能处理该URL"""
        ...

    async def scrape_async(self, url: ArticleURL) -> Article:
        """
        异步抓取文章

        Args:
            url: 文章URL

        Returns:
            抓取到的文章实体
        """
        ...
