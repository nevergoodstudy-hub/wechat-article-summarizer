"""历史记录页面

从 WechatSummarizerGUI 提取的历史记录页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from ..dialogs import (
    confirm_clear_cache,
    confirm_delete_history_article,
    show_clear_cache_error,
    show_clear_cache_success,
    show_delete_history_error,
)
from ..frames.history import HistoryHeaderFrame, HistoryListFrame

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

if TYPE_CHECKING:
    from ....domain.entities import Article


class HistoryPage(ctk.CTkFrame):
    """历史记录页面

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui

        # 公开属性
        self.cache_stats_label = None
        self.history_frame = None
        self.header_frame = None
        self.list_frame = None
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )

        self._build()

    def _build(self):
        """构建历史记录页面"""
        self.header_frame = HistoryHeaderFrame(
            self,
            on_refresh=self._refresh_history,
            on_clear=self._on_clear_cache,
        )
        self.header_frame.pack(fill="x", pady=(0, 20))
        self.cache_stats_label = self.header_frame.cache_stats_label

        self.list_frame = HistoryListFrame(self)
        self.list_frame.pack(fill="both", expand=True)
        self.history_frame = self.list_frame.history_frame

    # ── 历史记录业务逻辑（从 app.py 迁移） ─────────────────────

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """响应导航事件。"""
        _ = from_page
        if to_page == self.gui.PAGE_HISTORY:
            self.on_page_shown()

    def on_page_shown(self) -> None:
        """页面显示时刷新历史记录。"""
        self._refresh_history()

    def _refresh_history(self):
        """刷新历史记录列表"""
        self.list_frame.clear_items()
        storage = self.gui.container.storage
        if not storage:
            self.list_frame.show_storage_unavailable()
            return None
        try:
            stats = storage.get_stats()
            self.header_frame.update_cache_stats(
                total_entries=stats.total_entries,
                total_size_bytes=stats.total_size_bytes,
            )
            articles = storage.list_recent(limit=50)
            if not articles:
                self.list_frame.show_empty()
            else:
                for article in articles:
                    self._add_history_item(article)
        except Exception as e:
            logger.error(f"加载历史失败: {e}")
            self.list_frame.show_error(e)

    def _add_history_item(self, article: Article):
        """添加单条历史记录项"""
        self.list_frame.add_article(
            article,
            on_view=self._view_history_article,
            on_delete=self._delete_history_article,
        )

    def _view_history_article(self, article: Article):
        """查看历史文章 — 跨页导航委托给 GUI 控制器"""
        self.gui.current_article = article
        self.gui._show_page(self.gui.PAGE_SINGLE)
        self.gui._display_result(article)
        self.gui.url_entry.delete(0, "end")
        self.gui.url_entry.insert(0, str(article.url))

    def _delete_history_article(self, article: Article):
        """删除历史文章"""
        if not confirm_delete_history_article(article.title):
            return None
        try:
            storage = self.gui.container.storage
            if storage:
                storage.delete(article.id)
                self._refresh_history()
                logger.info(f"已删除: {article.title}")
        except Exception as e:
            show_delete_history_error(e)

    def _on_clear_cache(self):
        """清空所有缓存"""
        if not confirm_clear_cache():
            return None
        try:
            storage = self.gui.container.storage
            if storage:
                count = storage.clear_all()
                self._refresh_history()
                logger.info(f"已清空 {count} 条缓存")
                show_clear_cache_success(count)
        except Exception as e:
            show_clear_cache_error(e)
