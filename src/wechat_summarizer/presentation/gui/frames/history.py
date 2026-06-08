"""Reusable frame sections for the history page."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from ..styles.colors import ModernColors
from ..utils.i18n import tr

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - GUI dependency is optional at runtime
    ctk = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from ....domain.entities import Article


class HistoryHeaderFrame(ctk.CTkFrame):
    """History page title, cache stats, and primary actions."""

    def __init__(self, master, *, on_refresh: Callable[[], None], on_clear: Callable[[], None]):
        super().__init__(master, fg_color="transparent")
        self._on_refresh = on_refresh
        self._on_clear = on_clear
        self.cache_stats_label = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=tr("📜 历史记录"), font=ctk.CTkFont(size=24, weight="bold")).pack(
            side="left"
        )

        ctk.CTkButton(
            self,
            text=tr("🔄 刷新"),
            width=80,
            height=35,
            corner_radius=8,
            fg_color=ModernColors.NEUTRAL_BTN,
            command=self._on_refresh,
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            self,
            text=tr("🗑️ 清空缓存"),
            width=100,
            height=35,
            corner_radius=8,
            fg_color=ModernColors.ERROR,
            command=self._on_clear,
        ).pack(side="right", padx=5)

        self.cache_stats_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        )
        assert self.cache_stats_label is not None
        self.cache_stats_label.pack(side="right", padx=20)

    def update_cache_stats(self, *, total_entries: int, total_size_bytes: int) -> None:
        """Render cache statistics in the header."""
        assert self.cache_stats_label is not None
        self.cache_stats_label.configure(
            text=tr("缓存: {count} 条 | {size_kb:.1f} KB").format(
                count=total_entries,
                size_kb=total_size_bytes / 1024,
            )
        )


class HistoryListFrame(ctk.CTkFrame):
    """Card and scrollable list container for cached articles."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            corner_radius=15,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            **kwargs,
        )
        self.history_frame = None
        self._build()

    def _build(self) -> None:
        self.history_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.history_frame.pack(fill="both", expand=True, padx=15, pady=15)

    def clear_items(self) -> None:
        """Remove all rendered history entries."""
        for widget in self.history_frame.winfo_children():
            widget.destroy()

    def show_storage_unavailable(self) -> None:
        """Render the storage-unavailable empty state."""
        ctk.CTkLabel(self.history_frame, text=tr("缓存存储不可用"), text_color="gray").pack(pady=30)

    def show_empty(self) -> None:
        """Render the no-history empty state."""
        ctk.CTkLabel(self.history_frame, text=tr("暂无历史记录"), text_color="gray").pack(pady=30)

    def show_error(self, error: object) -> None:
        """Render a history loading error."""
        ctk.CTkLabel(
            self.history_frame,
            text=tr("加载失败: {error}").format(error=error),
            text_color=ModernColors.ERROR,
        ).pack(pady=30)

    def add_article(
        self,
        article: Article,
        *,
        on_view: Callable[[Article], None],
        on_delete: Callable[[Article], None],
    ) -> None:
        """Append a cached article row."""
        HistoryItemFrame(
            self.history_frame,
            article=article,
            on_view=on_view,
            on_delete=on_delete,
        ).pack(fill="x", pady=4)


class HistoryItemFrame(ctk.CTkFrame):
    """Single cached article row with view and delete actions."""

    def __init__(
        self,
        master,
        *,
        article: Article,
        on_view: Callable[[Article], None],
        on_delete: Callable[[Article], None],
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
            **kwargs,
        )
        self.article = article
        self._on_view = on_view
        self._on_delete = on_delete
        self._build()

    @staticmethod
    def format_title(title: str, *, max_length: int = 45) -> str:
        """Return a compact title for row display."""
        if len(title) <= max_length:
            return title
        return title[:max_length] + "..."

    @staticmethod
    def format_created_at(article: Article) -> str | None:
        """Return the cached article timestamp label."""
        if not article.created_at:
            return None
        return article.created_at.strftime("%m-%d %H:%M")

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=self.format_title(self.article.title),
            anchor="w",
            font=ctk.CTkFont(size=13),
        ).pack(side="left", padx=15, pady=10, fill="x", expand=True)

        time_str = self.format_created_at(self.article)
        if time_str:
            ctk.CTkLabel(
                self,
                text=time_str,
                text_color="gray",
                font=ctk.CTkFont(size=11),
            ).pack(side="left", padx=5)

        ctk.CTkButton(
            self,
            text=tr("查看"),
            width=60,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=ModernColors.INFO,
            command=lambda: self._on_view(self.article),
        ).pack(side="right", padx=5, pady=8)

        ctk.CTkButton(
            self,
            text=tr("删除"),
            width=60,
            height=28,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            fg_color=ModernColors.NEUTRAL_BTN,
            hover_color=ModernColors.ERROR,
            command=lambda: self._on_delete(self.article),
        ).pack(side="right", padx=2, pady=8)


__all__ = ["HistoryHeaderFrame", "HistoryItemFrame", "HistoryListFrame"]
