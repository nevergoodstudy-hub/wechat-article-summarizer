"""文章列表获取端口

定义获取公众号文章列表的抽象接口。
遵循六边形架构，将核心业务逻辑与外部实现解耦。
"""

from abc import abstractmethod
from typing import AsyncIterator, Protocol

from ....domain.entities.article_list import ArticleList, ArticleListItem
from ....domain.entities.official_account import OfficialAccount


class ArticleListPort(Protocol):
    """
    文章列表获取端口协议
    
    定义获取公众号文章列表的接口规范。
    支持分页获取和流式获取两种模式。
    """

    @abstractmethod
    async def get_article_list(
        self,
        account: OfficialAccount,
        begin: int = 0,
        count: int = 10,
    ) -> tuple[list[ArticleListItem], int]:
        """获取公众号文章列表（分页）
        
        Args:
            account: 目标公众号
            begin: 起始位置
            count: 获取数量（每次最多10条）
            
        Returns:
            (文章列表, 文章总数) 元组
            
        Raises:
            AuthenticationError: 认证失败
            RateLimitError: 请求频率过高
            NetworkError: 网络请求失败
        """
        ...

    @abstractmethod
    async def get_all_articles(
        self,
        account: OfficialAccount,
        max_count: int | None = None,
    ) -> ArticleList:
        """获取公众号全部文章
        
        自动处理分页，获取所有文章（或达到max_count限制）。
        
        Args:
            account: 目标公众号
            max_count: 最大获取数量（None表示获取全部）
            
        Returns:
            完整的文章列表聚合
            
        Raises:
            AuthenticationError: 认证失败
            RateLimitError: 请求频率过高
            NetworkError: 网络请求失败
        """
        ...

    @abstractmethod
    def stream_articles(
        self,
        account: OfficialAccount,
        max_count: int | None = None,
    ) -> AsyncIterator[ArticleListItem]:
        """流式获取文章（异步生成器）
        
        适用于需要逐条处理文章的场景，减少内存占用。
        
        Args:
            account: 目标公众号
            max_count: 最大获取数量
            
        Yields:
            文章列表项
            
        Raises:
            AuthenticationError: 认证失败
            RateLimitError: 请求频率过高
            NetworkError: 网络请求失败
        """
        ...

    @abstractmethod
    async def get_article_count(self, account: OfficialAccount) -> int:
        """获取公众号文章总数
        
        Args:
            account: 目标公众号
            
        Returns:
            文章总数
        """
        ...
