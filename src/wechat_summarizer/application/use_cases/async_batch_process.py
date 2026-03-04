"""异步批量处理用例

使用 asyncio.Semaphore 限制最大并发数，防止触发限流。
使用 asyncio.TaskGroup 批量执行异步任务（Python 3.11+ 结构化并发）。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

from ...domain.entities import Article
from ..ports.inbound import BatchProgress

if TYPE_CHECKING:
    from ...domain.value_objects import ArticleURL
    from ..ports.outbound import StoragePort, SummarizerPort
    from ..ports.outbound.scraper_port import AsyncScraperPort


@dataclass
class AsyncBatchResult:
    """异步批量处理结果"""

    articles: list[Article] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)  # (url, error_message)

    @property
    def success_count(self) -> int:
        return len(self.articles)

    @property
    def failed_count(self) -> int:
        return len(self.errors)

    @property
    def total(self) -> int:
        return self.success_count + self.failed_count


# 异步进度回调类型
AsyncProgressCallback = Callable[[BatchProgress], None]


class AsyncBatchProcessUseCase:
    """
    异步批量处理用例

    负责协调多篇文章的高并发异步处理。
    使用 Semaphore 控制最大并发数，避免被封禁。
    """

    def __init__(
        self,
        scrapers: list[AsyncScraperPort],
        summarizers: dict[str, SummarizerPort] | None = None,
        storage: StoragePort | None = None,
        max_concurrent: int = 5,
    ):
        """
        Args:
            scrapers: 异步抓取器列表（按优先级排序）
            summarizers: 摘要器字典（可选）
            storage: 存储（用于缓存，可选）
            max_concurrent: 最大并发数（默认 5）
        """
        self._scrapers = scrapers
        self._summarizers = summarizers or {}
        self._storage = storage
        self._max_concurrent = max_concurrent

    async def process_urls(
        self,
        urls: list[str],
        summarize: bool = True,
        method: str = "simple",
        on_progress: AsyncProgressCallback | None = None,
    ) -> AsyncBatchResult:
        """
        异步批量处理 URL 列表

        Args:
            urls: URL 列表
            summarize: 是否生成摘要
            method: 摘要方法
            on_progress: 进度回调函数

        Returns:
            批量处理结果
        """
        from ...domain.value_objects import ArticleURL

        progress = BatchProgress(total=len(urls))
        result = AsyncBatchResult()
        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def process_one(url: str) -> Article | None:
            """处理单个 URL（带信号量限制）"""
            async with semaphore:
                try:
                    # 解析 URL
                    article_url = ArticleURL.from_string(url)
                    normalized_url = str(article_url)

                    # 检查缓存
                    if self._storage is not None:
                        try:
                            cached = self._storage.get_by_url(normalized_url)
                            if cached is not None:
                                logger.info(f"缓存命中: {normalized_url}")
                                progress.mark_success(url)
                                if on_progress:
                                    on_progress(progress)
                                return cached
                        except Exception as e:
                            logger.warning(f"缓存读取失败，忽略: {e}")

                    # 选择并使用抓取器
                    article = await self._scrape_with_fallback(article_url)

                    if article is None:
                        raise Exception(f"没有可用的抓取器能处理URL: {url}")

                    # 生成摘要（同步，因为大多数 LLM 调用是同步的）
                    if summarize and article.content:
                        article = await self._summarize_article(article, method)

                    # 保存缓存
                    if self._storage is not None:
                        try:
                            self._storage.save(article)
                        except Exception as e:
                            logger.warning(f"缓存写入失败，忽略: {e}")

                    progress.mark_success(url)
                    if on_progress:
                        on_progress(progress)

                    return article

                except Exception as e:
                    logger.error(f"处理失败 {url}: {e}")
                    progress.mark_failed(url, str(e))
                    if on_progress:
                        on_progress(progress)
                    return None

        # 使用 TaskGroup 并发执行所有任务（结构化并发）
        # process_one 内部已捕获异常并返回 None，所以 TaskGroup 不会因单任务失败而取消全部
        task_results: list[Article | None] = []
        async with asyncio.TaskGroup() as tg:

            async def _collect(url: str) -> None:
                task_results.append(await process_one(url))

            for url in urls:
                tg.create_task(_collect(url))

        # 收集结果
        for res in task_results:
            if res is not None:
                result.articles.append(res)
            # res 为 None 的情况已经在 process_one 中记录了

        logger.info(
            f"异步批量处理完成: 成功 {result.success_count}/{result.total}, "
            f"失败 {result.failed_count}"
        )

        return result

    async def _scrape_with_fallback(self, url: ArticleURL) -> Article | None:
        """使用抓取器抓取，支持回退"""
        from ...shared.exceptions import ScraperError

        for scraper in self._scrapers:
            if scraper.can_handle(url):
                try:
                    logger.info(f"使用 {scraper.name} 异步抓取: {url}")
                    article = await scraper.scrape_async(url)
                    logger.info(f"抓取成功: {article.title} ({article.word_count}字)")
                    return article
                except ScraperError as e:
                    logger.warning(f"抓取器 {scraper.name} 失败: {e}, 尝试下一个...")
                    continue
                except Exception as e:
                    logger.warning(f"抓取器 {scraper.name} 异常: {e}, 尝试下一个...")
                    continue

        return None

    async def _summarize_article(self, article: Article, method: str) -> Article:
        """为文章生成摘要"""
        summarizer = self._summarizers.get(method)
        if summarizer is None:
            logger.warning(f"摘要器 {method} 不可用")
            return article

        if not summarizer.is_available():
            logger.warning(f"摘要器 {method} 当前不可用")
            return article

        try:
            # 在线程池中执行同步的摘要生成（避免阻塞事件循环）
            loop = asyncio.get_event_loop()
            content = article.content
            if content is None:
                logger.warning("文章内容为空，跳过摘要生成")
                return article
            summary = await loop.run_in_executor(
                None,
                lambda: summarizer.summarize(content),
            )
            article.attach_summary(summary)
            logger.info(f"摘要生成成功: {article.title}")
        except Exception as e:
            logger.warning(f"摘要生成失败: {e}")

        return article
