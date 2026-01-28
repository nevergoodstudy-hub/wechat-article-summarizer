"""摘要器出站端口 - 定义摘要器适配器必须实现的接口"""

from typing import Protocol, runtime_checkable

from ....domain.entities import Summary, SummaryMethod, SummaryStyle
from ....domain.value_objects import ArticleContent


@runtime_checkable
class SummarizerPort(Protocol):
    """
    摘要器端口

    定义摘要器适配器必须实现的接口。
    基础设施层的具体摘要器实现此接口。
    """

    @property
    def name(self) -> str:
        """摘要器名称"""
        ...

    @property
    def method(self) -> SummaryMethod:
        """摘要方法"""
        ...

    def is_available(self) -> bool:
        """
        检查摘要器是否可用

        Returns:
            是否可用（如API是否配置、服务是否在线等）
        """
        ...

    def summarize(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """
        生成摘要

        Args:
            content: 文章内容
            style: 摘要风格
            max_length: 最大字数

        Returns:
            生成的摘要

        Raises:
            SummarizerError: 摘要生成失败
        """
        ...


class AsyncSummarizerPort(Protocol):
    """
    异步摘要器端口
    """

    @property
    def name(self) -> str:
        """摘要器名称"""
        ...

    @property
    def method(self) -> SummaryMethod:
        """摘要方法"""
        ...

    def is_available(self) -> bool:
        """检查摘要器是否可用"""
        ...

    async def summarize_async(
        self,
        content: ArticleContent,
        style: SummaryStyle = SummaryStyle.CONCISE,
        max_length: int = 500,
    ) -> Summary:
        """异步生成摘要"""
        ...
