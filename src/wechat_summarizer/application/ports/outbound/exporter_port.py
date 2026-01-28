"""导出器出站端口 - 定义导出器适配器必须实现的接口"""

from typing import Protocol, runtime_checkable

from ....domain.entities import Article


@runtime_checkable
class ExporterPort(Protocol):
    """
    导出器端口

    定义导出器适配器必须实现的接口。
    """

    @property
    def name(self) -> str:
        """导出器名称"""
        ...

    @property
    def target(self) -> str:
        """导出目标标识 (html, markdown, onenote, notion, obsidian)"""
        ...

    def is_available(self) -> bool:
        """
        检查导出器是否可用

        Returns:
            是否可用（如认证是否有效等）
        """
        ...

    def export(
        self,
        article: Article,
        path: str | None = None,
        **options,
    ) -> str:
        """
        导出文章

        Args:
            article: 文章实体
            path: 导出路径（可选）
            **options: 额外选项

        Returns:
            导出结果（文件路径或成功消息）

        Raises:
            ExporterError: 导出失败
        """
        ...


class AsyncExporterPort(Protocol):
    """异步导出器端口"""

    @property
    def name(self) -> str:
        """导出器名称"""
        ...

    @property
    def target(self) -> str:
        """导出目标标识"""
        ...

    def is_available(self) -> bool:
        """检查导出器是否可用"""
        ...

    async def export_async(
        self,
        article: Article,
        path: str | None = None,
        **options,
    ) -> str:
        """异步导出文章"""
        ...
