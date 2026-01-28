"""批量导出端口

定义批量导出文章链接的抽象接口。
"""

from abc import abstractmethod
from pathlib import Path
from typing import Protocol

from ....domain.entities.article_list import ArticleList, ArticleListItem
from ....domain.value_objects.batch_export_options import BatchExportOptions


class BatchExportPort(Protocol):
    """
    批量导出端口协议
    
    定义批量导出文章链接的接口规范。
    支持多种导出格式（TXT、CSV、JSON、Markdown）。
    """

    @abstractmethod
    def export_links(
        self,
        items: list[ArticleListItem],
        options: BatchExportOptions,
        account_name: str | None = None,
    ) -> Path:
        """导出文章链接
        
        Args:
            items: 要导出的文章列表
            options: 导出选项
            account_name: 公众号名称（用于文件命名和分组）
            
        Returns:
            导出文件的路径
            
        Raises:
            IOError: 文件写入失败
        """
        ...

    @abstractmethod
    def export_article_list(
        self,
        article_list: ArticleList,
        options: BatchExportOptions,
    ) -> Path:
        """导出文章列表聚合
        
        Args:
            article_list: 文章列表聚合
            options: 导出选项
            
        Returns:
            导出文件的路径
        """
        ...

    @abstractmethod
    def export_multiple_accounts(
        self,
        article_lists: list[ArticleList],
        options: BatchExportOptions,
    ) -> Path:
        """导出多个公众号的文章
        
        Args:
            article_lists: 多个公众号的文章列表
            options: 导出选项
            
        Returns:
            导出文件的路径
        """
        ...

    @abstractmethod
    def format_link(
        self,
        item: ArticleListItem,
        options: BatchExportOptions,
    ) -> str:
        """格式化单个链接
        
        Args:
            item: 文章列表项
            options: 导出选项（决定链接格式）
            
        Returns:
            格式化后的链接字符串
        """
        ...
