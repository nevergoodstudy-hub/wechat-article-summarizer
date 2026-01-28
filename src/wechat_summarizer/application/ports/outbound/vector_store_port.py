"""向量存储出站端口 - 定义向量存储适配器必须实现的接口"""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class VectorDocument:
    """向量文档"""

    id: str
    text: str
    vector: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """搜索结果"""

    id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class VectorStorePort(Protocol):
    """
    向量存储端口

    定义向量存储适配器必须实现的接口。
    用于存储和检索向量化的文档。
    """

    @property
    def name(self) -> str:
        """存储名称"""
        ...

    def is_available(self) -> bool:
        """
        检查存储是否可用

        Returns:
            是否可用
        """
        ...

    def add(self, documents: list[VectorDocument]) -> None:
        """
        添加文档

        Args:
            documents: 向量文档列表

        Raises:
            VectorStoreError: 添加失败
        """
        ...

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        搜索相似文档

        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_metadata: 元数据过滤条件

        Returns:
            搜索结果列表，按相似度降序排列

        Raises:
            VectorStoreError: 搜索失败
        """
        ...

    def delete(self, ids: list[str]) -> None:
        """
        删除文档

        Args:
            ids: 文档ID列表

        Raises:
            VectorStoreError: 删除失败
        """
        ...

    def clear(self) -> None:
        """
        清空所有文档

        Raises:
            VectorStoreError: 清空失败
        """
        ...

    def count(self) -> int:
        """
        获取文档数量

        Returns:
            文档数量
        """
        ...


@runtime_checkable
class AsyncVectorStorePort(Protocol):
    """异步向量存储端口"""

    @property
    def name(self) -> str:
        """存储名称"""
        ...

    def is_available(self) -> bool:
        """检查是否可用"""
        ...

    async def add_async(self, documents: list[VectorDocument]) -> None:
        """异步添加文档"""
        ...

    async def search_async(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """异步搜索相似文档"""
        ...

    async def delete_async(self, ids: list[str]) -> None:
        """异步删除文档"""
        ...

    async def clear_async(self) -> None:
        """异步清空所有文档"""
        ...

    async def count_async(self) -> int:
        """异步获取文档数量"""
        ...
