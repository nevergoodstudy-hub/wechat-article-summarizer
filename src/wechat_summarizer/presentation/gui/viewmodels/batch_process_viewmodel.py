"""批量处理视图模型"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable

from .base import BaseViewModel, Command, Observable

if TYPE_CHECKING:
    from ....infrastructure.config import Container


class BatchItemStatus(Enum):
    """批量处理项状态"""

    PENDING = auto()  # 等待处理
    PROCESSING = auto()  # 处理中
    SUCCESS = auto()  # 成功
    FAILED = auto()  # 失败
    SKIPPED = auto()  # 跳过


@dataclass
class BatchItemModel:
    """批量处理项模型"""

    url: str
    status: BatchItemStatus = BatchItemStatus.PENDING
    title: str = ""
    error_message: str = ""
    output_path: str = ""


class BatchProcessViewModel(BaseViewModel):
    """批量处理视图模型

    负责管理批量文章处理流程。
    """

    def __init__(self, container: Container):
        super().__init__()
        self._container = container

        # 可观察属性
        self._items = Observable[list[BatchItemModel]]([])
        self._current_index = Observable(-1)
        self._total_count = Observable(0)
        self._success_count = Observable(0)
        self._failed_count = Observable(0)
        self._progress = Observable(0.0)

        # 配置选项
        self._selected_summarizer = Observable("simple")
        self._selected_exporter = Observable("html")
        self._no_summary = Observable(False)
        self._continue_on_error = Observable(True)

        # 内部状态
        self._cancel_requested = False

        # 命令
        self.add_urls_command = Command(
            execute=lambda: None,  # 需要参数，由视图层处理
            can_execute=lambda: not self.is_busy,
            description="添加URL",
        )
        self.clear_command = Command(
            execute=self.clear,
            can_execute=lambda: len(self._items.value) > 0 and not self.is_busy,
            description="清空列表",
        )
        self.start_command = Command(
            execute=self._do_start,
            can_execute=lambda: len(self._items.value) > 0 and not self.is_busy,
            description="开始处理",
        )
        self.cancel_command = Command(
            execute=self._do_cancel,
            can_execute=lambda: self.is_busy,
            description="取消处理",
        )

    # region Properties

    @property
    def items(self) -> list[BatchItemModel]:
        return self._items.value

    @property
    def current_index(self) -> int:
        return self._current_index.value

    @property
    def total_count(self) -> int:
        return self._total_count.value

    @property
    def success_count(self) -> int:
        return self._success_count.value

    @property
    def failed_count(self) -> int:
        return self._failed_count.value

    @property
    def progress(self) -> float:
        return self._progress.value

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

    @property
    def continue_on_error(self) -> bool:
        return self._continue_on_error.value

    @continue_on_error.setter
    def continue_on_error(self, value: bool) -> None:
        self._continue_on_error.value = value

    # endregion

    # region Subscriptions

    def subscribe_items(self, callback: Callable[[list[BatchItemModel], list[BatchItemModel]], None]) -> Callable[[], None]:
        return self._items.subscribe(callback)

    def subscribe_progress(self, callback: Callable[[float, float], None]) -> Callable[[], None]:
        return self._progress.subscribe(callback)

    # endregion

    # region Public Methods

    def add_urls(self, urls: list[str]) -> int:
        """添加URL列表

        Args:
            urls: URL列表

        Returns:
            实际添加的数量
        """
        added = 0
        current_urls = {item.url for item in self._items.value}

        new_items = list(self._items.value)
        for url in urls:
            url = url.strip()
            if url and url not in current_urls:
                new_items.append(BatchItemModel(url=url))
                current_urls.add(url)
                added += 1

        self._items.value = new_items
        self._total_count.value = len(new_items)
        return added

    def remove_item(self, index: int) -> None:
        """移除指定索引的项"""
        if 0 <= index < len(self._items.value):
            new_items = list(self._items.value)
            new_items.pop(index)
            self._items.value = new_items
            self._total_count.value = len(new_items)

    def clear(self) -> None:
        """清空所有项"""
        self._items.value = []
        self._total_count.value = 0
        self._success_count.value = 0
        self._failed_count.value = 0
        self._current_index.value = -1
        self._progress.value = 0.0
        self.reset()

    # endregion

    # region Commands

    def _do_start(self) -> None:
        """开始批量处理"""
        self._cancel_requested = False
        threading.Thread(target=self._process_batch_async, daemon=True).start()

    def _process_batch_async(self) -> None:
        """异步批量处理"""
        try:
            self.set_loading()
            self._success_count.value = 0
            self._failed_count.value = 0

            items = self._items.value
            total = len(items)

            for i, item in enumerate(items):
                if self._cancel_requested:
                    # 标记剩余项为跳过
                    for j in range(i, total):
                        self._update_item_status(j, BatchItemStatus.SKIPPED)
                    break

                self._current_index.value = i
                self._update_item_status(i, BatchItemStatus.PROCESSING)
                self._progress.value = i / total

                try:
                    # 抓取
                    article = self._container.fetch_use_case.execute(item.url)
                    self._update_item_title(i, article.title)

                    # 摘要（如果启用）
                    if not self.no_summary:
                        summary = self._container.summarize_use_case.execute(
                            article,
                            method=self.selected_summarizer,
                        )
                        article.attach_summary(summary)

                    # 导出
                    result = self._container.export_use_case.execute(
                        article,
                        target=self.selected_exporter,
                    )

                    self._update_item_output(i, str(result))
                    self._update_item_status(i, BatchItemStatus.SUCCESS)
                    self._success_count.value += 1

                except Exception as e:
                    self._update_item_error(i, str(e))
                    self._update_item_status(i, BatchItemStatus.FAILED)
                    self._failed_count.value += 1

                    if not self.continue_on_error:
                        # 标记剩余项为跳过
                        for j in range(i + 1, total):
                            self._update_item_status(j, BatchItemStatus.SKIPPED)
                        break

            self._progress.value = 1.0
            self._current_index.value = -1
            self.set_success()

        except Exception as e:
            self.set_error(f"批量处理失败: {e}")

    def _do_cancel(self) -> None:
        """取消批量处理"""
        self._cancel_requested = True

    # endregion

    # region Helpers

    def _update_item_status(self, index: int, status: BatchItemStatus) -> None:
        """更新项状态（触发通知）"""
        if 0 <= index < len(self._items.value):
            self._items.value[index].status = status
            # 触发列表更新通知
            self._items.value = list(self._items.value)

    def _update_item_title(self, index: int, title: str) -> None:
        """更新项标题"""
        if 0 <= index < len(self._items.value):
            self._items.value[index].title = title

    def _update_item_error(self, index: int, error: str) -> None:
        """更新项错误信息"""
        if 0 <= index < len(self._items.value):
            self._items.value[index].error_message = error

    def _update_item_output(self, index: int, output_path: str) -> None:
        """更新项输出路径"""
        if 0 <= index < len(self._items.value):
            self._items.value[index].output_path = output_path

    # endregion
