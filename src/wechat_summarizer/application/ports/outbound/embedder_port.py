"""向量嵌入器出站端口 - 定义嵌入器适配器必须实现的接口"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbedderPort(Protocol):
    """
    向量嵌入器端口

    定义向量嵌入器适配器必须实现的接口。
    用于将文本转换为向量表示，支持语义检索。
    """

    @property
    def name(self) -> str:
        """嵌入器名称"""
        ...

    @property
    def dimension(self) -> int:
        """向量维度"""
        ...

    def is_available(self) -> bool:
        """
        检查嵌入器是否可用

        Returns:
            是否可用（如API是否配置、模型是否加载等）
        """
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        批量嵌入文本

        Args:
            texts: 文本列表

        Returns:
            向量列表，每个向量是浮点数列表

        Raises:
            EmbedderError: 嵌入失败
        """
        ...

    def embed_single(self, text: str) -> list[float]:
        """
        嵌入单个文本

        Args:
            text: 文本

        Returns:
            向量表示

        Raises:
            EmbedderError: 嵌入失败
        """
        ...


@runtime_checkable
class AsyncEmbedderPort(Protocol):
    """异步向量嵌入器端口"""

    @property
    def name(self) -> str:
        """嵌入器名称"""
        ...

    @property
    def dimension(self) -> int:
        """向量维度"""
        ...

    def is_available(self) -> bool:
        """检查是否可用"""
        ...

    async def embed_async(self, texts: list[str]) -> list[list[float]]:
        """异步批量嵌入文本"""
        ...

    async def embed_single_async(self, text: str) -> list[float]:
        """异步嵌入单个文本"""
        ...
