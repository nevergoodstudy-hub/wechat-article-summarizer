"""文章列表获取器

实现获取微信公众号文章列表的功能，调用微信公众平台的 appmsg 接口。
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

import httpx
from loguru import logger

from ....application.ports.outbound.article_list_port import ArticleListPort
from ....domain.entities.article_list import ArticleList, ArticleListItem
from ....domain.entities.official_account import OfficialAccount
from ....infrastructure.config.settings import get_settings
from ..http_client_pool import get_http_pool
from .auth_manager import WechatAuthManager
from .rate_limiter import RateLimiter, RateLimitConfig


# 微信文章列表API
APPMSG_URL = "https://mp.weixin.qq.com/cgi-bin/appmsg"


class WechatArticleFetcher:
    """
    文章列表获取器
    
    调用微信公众平台的 /cgi-bin/appmsg 接口获取公众号文章列表。
    支持分页获取和流式获取两种模式。
    
    使用方法:
        auth = WechatAuthManager(storage)
        fetcher = WechatArticleFetcher(auth)
        
        # 获取指定公众号的所有文章
        account = OfficialAccount(fakeid="xxx", nickname="测试号")
        article_list = await fetcher.get_all_articles(account, max_count=100)
        
        for item in article_list:
            print(f"{item.title}: {item.link}")
    """

    def __init__(
        self,
        auth_manager: WechatAuthManager,
        rate_limiter: RateLimiter | None = None,
        cache: "ArticleListCache | None" = None,
    ) -> None:
        """初始化获取器
        
        Args:
            auth_manager: 认证管理器（必须已登录）
            rate_limiter: 频率限制器（可选）
            cache: 文章列表缓存（可选）
        """
        self._auth = auth_manager
        self._settings = get_settings()
        
        self._rate_limiter = rate_limiter or RateLimiter(
            RateLimitConfig(
                requests_per_minute=self._settings.batch.max_requests_per_minute,
                min_interval=self._settings.batch.request_interval,
                max_interval=self._settings.batch.retry_delay,
            )
        )
        
        self._cache = cache
        self._client: httpx.AsyncClient | None = None

    @property
    def is_authenticated(self) -> bool:
        """是否已认证"""
        return self._auth.is_authenticated

    async def _get_client(self) -> httpx.AsyncClient:
        """获取配置好的HTTP客户端"""
        if self._client is None:
            pool = get_http_pool()
            self._client = await pool.get_client("mp.weixin.qq.com")
        return self._client

    def _prepare_cookies(self, client: httpx.AsyncClient) -> None:
        """设置认证Cookies"""
        if not self._auth.credentials:
            raise ValueError("未登录，请先完成认证")
        
        for name, value in self._auth.credentials.cookies.items():
            client.cookies.set(name, value)

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
            ValueError: 未登录
            RuntimeError: API调用失败
        """
        if not self.is_authenticated:
            raise ValueError("未登录，请先完成认证")
        
        client = await self._get_client()
        self._prepare_cookies(client)
        
        # 应用频率限制
        async with self._rate_limiter:
            try:
                response = await self._do_fetch(
                    client, account.fakeid, begin, min(count, 10)
                )
                
                items, total = self._parse_response(response)
                
                logger.debug(
                    f"获取 {account.nickname} 文章: "
                    f"begin={begin}, count={len(items)}, total={total}"
                )
                
                return items, total
                
            except Exception as e:
                logger.error(f"获取文章列表失败: {e}")
                raise RuntimeError(f"获取文章列表失败: {e}") from e

    async def _do_fetch(
        self,
        client: httpx.AsyncClient,
        fakeid: str,
        begin: int,
        count: int,
    ) -> dict:
        """执行获取请求"""
        token = self._auth.token
        if not token:
            raise ValueError("Token无效")
        
        params = {
            "action": "list_ex",
            "begin": begin,
            "count": count,
            "fakeid": fakeid,
            "type": "9",  # 图文消息
            "query": "",
            "token": token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
        }
        
        response = await client.get(APPMSG_URL, params=params)
        
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")
        
        data = response.json()
        
        # 检查API返回状态
        base_resp = data.get("base_resp", {})
        ret = base_resp.get("ret", -1)
        
        if ret != 0:
            err_msg = base_resp.get("err_msg", "未知错误")
            
            # 特定错误码处理
            if ret == 200040:
                raise ValueError("登录状态已失效，请重新登录")
            elif ret == 200013:
                raise RuntimeError("请求频率过高，请稍后重试")
            elif ret == 64004:
                raise RuntimeError("获取文章列表失败：无权限或公众号不存在")
            else:
                raise RuntimeError(f"API错误 ({ret}): {err_msg}")
        
        return data

    def _parse_response(self, response: dict) -> tuple[list[ArticleListItem], int]:
        """解析API响应"""
        items = []
        
        app_msg_list = response.get("app_msg_list", [])
        total_count = response.get("app_msg_cnt", 0)
        
        for item_data in app_msg_list:
            try:
                item = ArticleListItem.from_api_response(item_data)
                items.append(item)
            except Exception as e:
                logger.warning(f"解析文章数据失败: {e}, data={item_data}")
                continue
        
        return items, total_count

    async def get_all_articles(
        self,
        account: OfficialAccount,
        max_count: int | None = None,
        use_cache: bool = True,
    ) -> ArticleList:
        """获取公众号全部文章
        
        自动处理分页，获取所有文章（或达到max_count限制）。
        
        Args:
            account: 目标公众号
            max_count: 最大获取数量（None表示获取全部，受配置限制）
            use_cache: 是否使用缓存
            
        Returns:
            完整的文章列表聚合
        """
        # 检查缓存
        if use_cache and self._cache:
            cached = self._cache.get(account.fakeid)
            if cached:
                logger.info(f"使用缓存的文章列表: {account.nickname}")
                return cached
        
        # 应用配置限制
        limit = max_count or self._settings.batch.max_articles_per_account
        page_size = self._settings.batch.page_size
        
        article_list = ArticleList(
            fakeid=account.fakeid,
            account_name=account.nickname,
        )
        
        begin = 0
        total_fetched = 0
        
        while True:
            items, total_count = await self.get_article_list(
                account, begin=begin, count=page_size
            )
            
            # 更新总数
            article_list.total_count = total_count
            
            if not items:
                break
            
            # 添加文章
            added = article_list.add_items(items)
            total_fetched += added
            
            logger.info(
                f"获取 {account.nickname} 文章进度: "
                f"{article_list.count}/{total_count}"
            )
            
            # 检查是否达到限制
            if total_fetched >= limit:
                logger.info(f"达到获取限制 ({limit})，停止获取")
                break
            
            # 检查是否已获取全部
            if article_list.count >= total_count:
                break
            
            begin += page_size
        
        # 保存到缓存
        if self._cache:
            self._cache.set(account.fakeid, article_list)
        
        logger.info(
            f"完成获取 {account.nickname}: "
            f"共 {article_list.count}/{article_list.total_count} 篇文章"
        )
        
        return article_list

    async def stream_articles(
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
        """
        limit = max_count or self._settings.batch.max_articles_per_account
        page_size = self._settings.batch.page_size
        
        begin = 0
        yielded = 0
        
        while True:
            items, total_count = await self.get_article_list(
                account, begin=begin, count=page_size
            )
            
            if not items:
                break
            
            for item in items:
                yield item
                yielded += 1
                
                if yielded >= limit:
                    return
            
            if begin + len(items) >= total_count:
                break
            
            begin += page_size

    async def get_article_count(self, account: OfficialAccount) -> int:
        """获取公众号文章总数
        
        Args:
            account: 目标公众号
            
        Returns:
            文章总数
        """
        # 获取第一页以获取总数
        _, total = await self.get_article_list(account, begin=0, count=1)
        return total

    async def fetch_multiple_accounts(
        self,
        accounts: list[OfficialAccount],
        max_count_per_account: int | None = None,
        max_concurrency: int = 3,
        use_cache: bool = True,
    ) -> dict[str, ArticleList]:
        """并发获取多个公众号的文章列表
        
        使用 asyncio.Semaphore 控制并发数量，
        配合 asyncio.gather 实现高效并发获取。
        
        Args:
            accounts: 要获取的公众号列表
            max_count_per_account: 每个公众号最大获取数量
            max_concurrency: 最大并发数（默认3，避免触发频率限制）
            use_cache: 是否使用缓存
            
        Returns:
            {fakeid: ArticleList} 的字典
            
        Example:
            accounts = [account1, account2, account3]
            results = await fetcher.fetch_multiple_accounts(accounts, max_count_per_account=50)
            for fakeid, article_list in results.items():
                print(f"{article_list.account_name}: {article_list.count} 篇")
        """
        if not accounts:
            return {}
        
        # 使用信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrency)
        results: dict[str, ArticleList] = {}
        errors: dict[str, str] = {}
        
        async def fetch_one(account: OfficialAccount) -> tuple[str, ArticleList | None, str | None]:
            """(并发安全) 获取单个公众号的文章"""
            async with semaphore:  # 控制并发
                try:
                    article_list = await self.get_all_articles(
                        account,
                        max_count=max_count_per_account,
                        use_cache=use_cache,
                    )
                    return (account.fakeid, article_list, None)
                except Exception as e:
                    logger.error(f"获取 {account.nickname} 文章失败: {e}")
                    return (account.fakeid, None, str(e))
        
        # 创建所有任务
        tasks = [fetch_one(account) for account in accounts]
        
        # 并发执行
        logger.info(f"开始并发获取 {len(accounts)} 个公众号（并发数: {max_concurrency}）")
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集结果
        success_count = 0
        for result in completed:
            if isinstance(result, Exception):
                logger.error(f"并发任务异常: {result}")
                continue
            
            fakeid, article_list, error = result
            if article_list:
                results[fakeid] = article_list
                success_count += 1
            elif error:
                errors[fakeid] = error
        
        logger.info(
            f"并发获取完成: 成功 {success_count}/{len(accounts)}"
        )
        
        return results

    async def close(self) -> None:
        """关闭连接"""
        self._client = None
