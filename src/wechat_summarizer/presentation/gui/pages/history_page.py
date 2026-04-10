"""历史记录页面

从 WechatSummarizerGUI 提取的历史记录页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。
"""

from __future__ import annotations

from tkinter import messagebox
from typing import TYPE_CHECKING

from loguru import logger

from ..styles.colors import ModernColors
from ..utils.i18n import tr

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
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )

        self._build()

    def _build(self):
        """构建历史记录页面"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=tr("📜 历史记录"), font=ctk.CTkFont(size=24, weight="bold")).pack(
            side="left"
        )

        ctk.CTkButton(
            header,
            text=tr("🔄 刷新"),
            width=80,
            height=35,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=self._refresh_history,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            header,
            text=tr("🗑️ 清空缓存"),
            width=100,
            height=35,
            corner_radius=8,
            fg_color=ModernColors.ERROR,
            command=self._on_clear_cache,
        ).pack(side="right", padx=5)

        self.cache_stats_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        )
        self.cache_stats_label.pack(side="right", padx=20)

        list_card = ctk.CTkFrame(
            self, corner_radius=15, fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD)
        )
        list_card.pack(fill="both", expand=True)

        self.history_frame = ctk.CTkScrollableFrame(list_card, corner_radius=10)
        self.history_frame.pack(fill="both", expand=True, padx=15, pady=15)

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
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        storage = self.gui.container.storage
        if not storage:
            ctk.CTkLabel(self.history_frame, text="缓存存储不可用", text_color="gray").pack(pady=30)
            return None
        try:
            stats = storage.get_stats()
            self.cache_stats_label.configure(
                text=f"缓存: {stats.total_entries} 条 | {stats.total_size_bytes / 1024:.1f} KB"
            )
            articles = storage.list_recent(limit=50)
            if not articles:
                ctk.CTkLabel(self.history_frame, text="暂无历史记录", text_color="gray").pack(
                    pady=30
                )
            else:
                for article in articles:
                    self._add_history_item(article)
        except Exception as e:
            logger.error(f"加载历史失败: {e}")
            ctk.CTkLabel(
                self.history_frame, text=f"加载失败: {e}", text_color=ModernColors.ERROR
            ).pack(pady=30)

    def _add_history_item(self, article: Article):
        """添加单条历史记录项"""
        frame = ctk.CTkFrame(self.history_frame, corner_radius=10, fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET))
        frame.pack(fill="x", pady=4)
        title = article.title[:45] + "..." if len(article.title) > 45 else article.title
        ctk.CTkLabel(frame, text=title, anchor="w", font=ctk.CTkFont(size=13)).pack(
            side="left", padx=15, pady=10, fill="x", expand=True
        )
        if article.created_at:
            time_str = article.created_at.strftime("%m-%d %H:%M")
            ctk.CTkLabel(frame, text=time_str, text_color="gray", font=ctk.CTkFont(size=11)).pack(
                side="left", padx=5
            )
        ctk.CTkButton(
            frame,
            text="查看",
            width=60,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=ModernColors.INFO,
            command=lambda a=article: self._view_history_article(a),
        ).pack(side="right", padx=5, pady=8)
        ctk.CTkButton(
            frame,
            text="删除",
            width=60,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=ModernColors.NEUTRAL_BTN,
            hover_color=ModernColors.ERROR,
            command=lambda a=article: self._delete_history_article(a),
        ).pack(side="right", padx=2, pady=8)

    def _view_history_article(self, article: Article):
        """查看历史文章 — 跨页导航委托给 GUI 控制器"""
        self.gui.current_article = article
        self.gui._show_page(self.gui.PAGE_SINGLE)
        self.gui._display_result(article)
        self.gui.url_entry.delete(0, "end")
        self.gui.url_entry.insert(0, str(article.url))

    def _delete_history_article(self, article: Article):
        """删除历史文章"""
        if not messagebox.askyesno("确认", f'删除 "{article.title[:25]}..." ?'):
            return None
        try:
            storage = self.gui.container.storage
            if storage:
                storage.delete(article.id)
                self._refresh_history()
                logger.info(f"已删除: {article.title}")
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")

    def _on_clear_cache(self):
        """清空所有缓存"""
        if not messagebox.askyesno("确认", "确定清空所有缓存？此操作不可撤销。"):
            return None
        try:
            storage = self.gui.container.storage
            if storage:
                count = storage.clear_all()
                self._refresh_history()
                logger.info(f"已清空 {count} 条缓存")
                messagebox.showinfo("成功", f"已清空 {count} 条缓存")
        except Exception as e:
            messagebox.showerror("错误", f"清空失败: {e}")
