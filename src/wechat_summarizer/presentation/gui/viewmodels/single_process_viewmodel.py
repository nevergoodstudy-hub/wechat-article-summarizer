"""单篇文章处理视图模型"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING

from ..utils.i18n import tr
from .base import BaseViewModel, Command, Observable
from .single_process_availability import (
    get_available_exporters as resolve_available_exporters,
)
from .single_process_availability import (
    get_available_summarizers as resolve_available_summarizers,
)
from .single_process_availability import (
    get_exporter_unavailable_reason,
    get_summarizer_unavailable_reason,
)
from .single_process_mapping import convert_article, convert_summary
from .single_process_models import ArticleDisplayModel, SummaryDisplayModel

if TYPE_CHECKING:
    from ....domain.entities import Article, Summary
    from .ports import ContainerLike


class SingleProcessViewModel(BaseViewModel):
    """单篇文章处理视图模型

    负责管理单篇文章的抓取、摘要生成和导出流程。
    """

    def __init__(self, container: ContainerLike):
        super().__init__()
        self._container = container

        # 可观察属性
        self._url = Observable("")
        self._article = Observable[ArticleDisplayModel | None](None)
        self._summary = Observable[SummaryDisplayModel | None](None)
        self._progress = Observable(0.0)
        self._progress_text = Observable("")

        # 配置选项
        self._selected_summarizer = Observable("simple")
        self._selected_exporter = Observable("html")
        self._no_summary = Observable(False)

        # 内部状态
        self._current_article: Article | None = None
        self._cancel_requested = False

        # 命令
        self.fetch_command = Command(
            execute=self._do_fetch,
            can_execute=lambda: bool(self._url.value) and not self.is_busy,
            description=tr("抓取文章"),
        )
        self.summarize_command = Command(
            execute=self._do_summarize,
            can_execute=lambda: self._current_article is not None and not self.is_busy,
            description=tr("生成摘要"),
        )
        self.export_command = Command(
            execute=self._do_export,
            can_execute=lambda: self._current_article is not None and not self.is_busy,
            description=tr("导出文章"),
        )
        self.process_all_command = Command(
            execute=self._do_process_all,
            can_execute=lambda: bool(self._url.value) and not self.is_busy,
            description=tr("一键处理"),
        )
        self.cancel_command = Command(
            execute=self._do_cancel,
            can_execute=lambda: self.is_busy,
            description=tr("取消操作"),
        )

    # region Properties

    @property
    def url(self) -> str:
        return self._url.value

    @url.setter
    def url(self, value: str) -> None:
        self._url.value = value.strip()

    @property
    def article(self) -> ArticleDisplayModel | None:
        return self._article.value

    @property
    def summary(self) -> SummaryDisplayModel | None:
        return self._summary.value

    @property
    def progress(self) -> float:
        return self._progress.value

    @property
    def progress_text(self) -> str:
        return self._progress_text.value

    @property
    def selected_summarizer(self) -> str:
        return self._selected_summarizer.value

    @selected_summarizer.setter
    def selected_summarizer(self, value: str) -> None:
        self._selected_summarizer.value = value

    @property
    def selected_exporter(self) -> str:
        return self._selected_exporter.value

    @selected_exporter.setter
    def selected_exporter(self, value: str) -> None:
        self._selected_exporter.value = value

    @property
    def no_summary(self) -> bool:
        return self._no_summary.value

    @no_summary.setter
    def no_summary(self, value: bool) -> None:
        self._no_summary.value = value

    # endregion

    # region Subscriptions

    def subscribe_url(self, callback: Callable[[str, str], None]) -> Callable[[], None]:
        return self._url.subscribe(callback)

    def subscribe_article(
        self, callback: Callable[[ArticleDisplayModel | None, ArticleDisplayModel | None], None]
    ) -> Callable[[], None]:
        return self._article.subscribe(callback)

    def subscribe_summary(
        self, callback: Callable[[SummaryDisplayModel | None, SummaryDisplayModel | None], None]
    ) -> Callable[[], None]:
        return self._summary.subscribe(callback)

    def subscribe_progress(self, callback: Callable[[float, float], None]) -> Callable[[], None]:
        return self._progress.subscribe(callback)

    def subscribe_progress_text(self, callback: Callable[[str, str], None]) -> Callable[[], None]:
        return self._progress_text.subscribe(callback)

    # endregion

    # region Commands

    def _do_fetch(self) -> None:
        """在后台线程中执行抓取"""
        self._cancel_requested = False
        threading.Thread(target=self._fetch_async, daemon=True).start()

    def _fetch_async(self) -> None:
        """异步抓取文章"""
        try:
            self.set_loading()
            self._update_progress(0.1, tr("正在抓取文章..."))

            article = self._container.fetch_use_case.execute(self.url)

            if self._cancel_requested:
                self.reset()
                return

            self._current_article = article
            self._article.value = self._convert_article(article)
            self._update_progress(1.0, tr("抓取完成"))
            self.set_success()

        except Exception as e:
            self.set_error(tr("抓取失败: {error}").format(error=e))

    def _do_summarize(self) -> None:
        """在后台线程中执行摘要生成"""
        if self._current_article is None:
            return
        self._cancel_requested = False
        threading.Thread(target=self._summarize_async, daemon=True).start()

    def _summarize_async(self) -> None:
        """异步生成摘要"""
        if self._current_article is None:
            return

        try:
            self.set_loading()
            self._update_progress(0.3, tr("正在生成摘要..."))

            summary = self._container.summarize_use_case.execute(
                self._current_article,
                method=self.selected_summarizer,
            )

            if self._cancel_requested:
                self.reset()
                return

            self._current_article.attach_summary(summary)
            self._summary.value = self._convert_summary(summary)
            self._update_progress(1.0, tr("摘要生成完成"))
            self.set_success()

        except Exception as e:
            self.set_error(tr("摘要生成失败: {error}").format(error=e))

    def _do_export(self) -> None:
        """在后台线程中执行导出"""
        if self._current_article is None:
            return
        self._cancel_requested = False
        threading.Thread(target=self._export_async, daemon=True).start()

    def _export_async(self) -> None:
        """异步导出"""
        if self._current_article is None:
            return

        try:
            self.set_loading()
            self._update_progress(0.5, tr("正在导出..."))

            result = self._container.export_use_case.execute(
                self._current_article,
                target=self.selected_exporter,
            )

            if self._cancel_requested:
                self.reset()
                return

            self._update_progress(1.0, tr("已导出: {path}").format(path=result))
            self.set_success()

        except Exception as e:
            self.set_error(tr("导出失败: {error}").format(error=e))

    def _do_process_all(self) -> None:
        """一键处理：抓取 + 摘要 + 导出"""
        self._cancel_requested = False
        threading.Thread(target=self._process_all_async, daemon=True).start()

    def _process_all_async(self) -> None:
        """异步一键处理"""
        try:
            self.set_loading()

            # 步骤1: 抓取
            self._update_progress(0.1, tr("正在抓取文章..."))
            article = self._container.fetch_use_case.execute(self.url)
            self._current_article = article
            self._article.value = self._convert_article(article)

            if self._cancel_requested:
                self.reset()
                return

            # 步骤2: 摘要（如果启用）
            if not self.no_summary:
                self._update_progress(0.4, tr("正在生成摘要..."))
                summary = self._container.summarize_use_case.execute(
                    article,
                    method=self.selected_summarizer,
                )
                article.attach_summary(summary)
                self._summary.value = self._convert_summary(summary)

                if self._cancel_requested:
                    self.reset()
                    return

            # 步骤3: 导出
            self._update_progress(0.8, tr("正在导出..."))
            result = self._container.export_use_case.execute(
                article,
                target=self.selected_exporter,
            )

            self._update_progress(1.0, tr("处理完成: {path}").format(path=result))
            self.set_success()

        except Exception as e:
            self.set_error(tr("处理失败: {error}").format(error=e))

    def _do_cancel(self) -> None:
        """请求取消当前操作"""
        self._cancel_requested = True
        self._update_progress(0, tr("正在取消..."))

    # endregion

    # region Helpers

    def _update_progress(self, value: float, text: str) -> None:
        """更新进度"""
        self._progress.value = value
        self._progress_text.value = text

    @staticmethod
    def _convert_article(article: Article) -> ArticleDisplayModel:
        """转换文章为显示模型"""
        return convert_article(article)

    @staticmethod
    def _convert_summary(summary: Summary) -> SummaryDisplayModel:
        """转换摘要为显示模型"""
        return convert_summary(summary)

    def clear(self) -> None:
        """清空所有数据"""
        self._url.value = ""
        self._article.value = None
        self._summary.value = None
        self._current_article = None
        self._update_progress(0, "")
        self.reset()

    # endregion

    def get_available_summarizers(self) -> list[tuple[str, bool, str]]:
        """获取可用的摘要器列表

        Returns:
            列表，每项为 (名称, 是否可用, 不可用原因)
        """
        return resolve_available_summarizers(self._container)

    def get_available_exporters(self) -> list[tuple[str, bool, str]]:
        """获取可用的导出器列表

        Returns:
            列表，每项为 (名称, 是否可用, 不可用原因)
        """
        return resolve_available_exporters(self._container)

    def _get_summarizer_unavailable_reason(self, name: str) -> str:
        """获取摘要器不可用原因"""
        return get_summarizer_unavailable_reason(name)

    def _get_exporter_unavailable_reason(self, name: str) -> str:
        """获取导出器不可用原因"""
        return get_exporter_unavailable_reason(name)


__all__ = ["ArticleDisplayModel", "SingleProcessViewModel", "SummaryDisplayModel"]
