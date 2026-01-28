"""批量处理用例"""

from __future__ import annotations

from collections.abc import Iterator

from loguru import logger

from ...domain.entities import Article
from ..ports.inbound import BatchProgress, ProgressCallback
from .export_article import ExportArticleUseCase
from .fetch_article import FetchArticleUseCase
from .summarize_article import SummarizeArticleUseCase


class BatchProcessUseCase:
    """
    批量处理用例

    负责协调多篇文章的批量处理。
    """

    def __init__(
        self,
        fetch_use_case: FetchArticleUseCase,
        summarize_use_case: SummarizeArticleUseCase,
        export_use_case: ExportArticleUseCase,
    ):
        self._fetch = fetch_use_case
        self._summarize = summarize_use_case
        self._export = export_use_case

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
        progress = BatchProgress(total=len(urls))

        for url in urls:
            try:
                # 抓取文章
                article = self._fetch.execute(url)

                # 生成摘要
                if summarize and article.content:
                    try:
                        summary = self._summarize.execute(article, method=method)
                        article.attach_summary(summary)
                    except Exception as e:
                        logger.warning(f"摘要生成失败: {e}")

                progress.mark_success(url)

                if on_progress:
                    on_progress(progress)

                yield article

            except Exception as e:
                logger.error(f"处理失败 {url}: {e}")
                progress.mark_failed(url, str(e))

                if on_progress:
                    on_progress(progress)

        logger.info(
            f"批量处理完成: 成功 {progress.success}/{progress.total}, 失败 {progress.failed}"
        )

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
        results = []

        for article in articles:
            try:
                result = self._export.execute(
                    article,
                    target=target,
                    path=output_dir,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"导出失败 {article.title}: {e}")
                results.append(f"导出失败: {e}")

        return results
