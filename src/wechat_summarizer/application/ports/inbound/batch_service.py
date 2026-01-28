"""批量处理服务入站端口"""

from collections.abc import Callable, Iterator
from typing import Protocol

from ....domain.entities import Article


class BatchProgress:
    """批量处理进度"""

    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.success = 0
        self.failed = 0
        self.current_url: str = ""
        self.errors: list[tuple[str, str]] = []  # (url, error_message)

    @property
    def progress_percent(self) -> float:
        if self.total == 0:
            return 100.0
        return (self.completed / self.total) * 100

    def mark_success(self, url: str) -> None:
        self.completed += 1
        self.success += 1
        self.current_url = url

    def mark_failed(self, url: str, error: str) -> None:
        self.completed += 1
        self.failed += 1
        self.current_url = url
        self.errors.append((url, error))


# 进度回调类型
ProgressCallback = Callable[[BatchProgress], None]


class BatchServicePort(Protocol):
    """
    批量处理服务端口

    定义批量处理文章的服务接口。
    """

    def process_urls(
        self,
        urls: list[str],
        summarize: bool = True,
        method: str = "simple",
        on_progress: ProgressCallback | None = None,
    ) -> Iterator[Article]:
        """
        批量处理URL列表

        Args:
            urls: URL列表
            summarize: 是否生成摘要
            method: 摘要方法
            on_progress: 进度回调函数

        Yields:
            处理完成的文章
        """
        ...

    def process_rss(
        self,
        feed_url: str,
        limit: int = 10,
        summarize: bool = True,
        method: str = "simple",
        on_progress: ProgressCallback | None = None,
    ) -> Iterator[Article]:
        """
        处理RSS订阅

        Args:
            feed_url: RSS订阅URL
            limit: 最大处理数量
            summarize: 是否生成摘要
            method: 摘要方法
            on_progress: 进度回调函数

        Yields:
            处理完成的文章
        """
        ...

    def export_batch(
        self,
        articles: list[Article],
        target: str,
        output_dir: str | None = None,
    ) -> list[str]:
        """
        批量导出文章

        Args:
            articles: 文章列表
            target: 导出目标
            output_dir: 输出目录

        Returns:
            导出结果列表
        """
        ...
