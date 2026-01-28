"""存储出站端口 - 定义存储适配器必须实现的接口"""

from typing import Protocol, runtime_checkable
from uuid import UUID

from ....domain.entities import Article


@runtime_checkable
class StoragePort(Protocol):
    """
    存储端口

    定义存储适配器必须实现的接口。
    用于文章的持久化存储和检索。
    """

    def save(self, article: Article) -> None:
        """
        保存文章

        Args:
            article: 文章实体

        Raises:
            StorageError: 保存失败
        """
        ...

    def get(self, article_id: UUID) -> Article | None:
        """
        获取文章

        Args:
            article_id: 文章ID

        Returns:
            文章实体，不存在返回None
        """
        ...

    def get_by_url(self, url: str) -> Article | None:
        """
        通过URL获取文章

        Args:
            url: 文章URL

        Returns:
            文章实体，不存在返回None
        """
        ...

    def list_recent(self, limit: int = 20) -> list[Article]:
        """
        获取最近的文章列表

        Args:
            limit: 最大数量

        Returns:
            文章列表
        """
        ...

    def delete(self, article_id: UUID) -> bool:
        """
        删除文章

        Args:
            article_id: 文章ID

        Returns:
            是否删除成功
        """
        ...

    def exists(self, url: str) -> bool:
        """
        检查文章是否已存在

        Args:
            url: 文章URL

        Returns:
            是否存在
        """
        ...
