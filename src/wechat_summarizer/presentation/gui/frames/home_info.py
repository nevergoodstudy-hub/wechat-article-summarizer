"""Home dashboard status and recent-record sections."""

from __future__ import annotations

import contextlib
from typing import Any

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class HomeInfoRowFrame(ctk.CTkFrame):
    """Dashboard status and recent-record row."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        pages: dict[str, str],
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.pages = pages
        self._build()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.status_overview = HomeStatusOverviewFrame(
            self,
            gui=self.gui,
            page_settings=self.pages["settings"],
        )
        self.status_overview.grid(row=0, column=0, padx=(8, 6), pady=8, sticky="nsew")

        self.recent_records = HomeRecentRecordsFrame(
            self,
            gui=self.gui,
            page_history=self.pages["history"],
        )
        self.recent_records.grid(row=0, column=1, padx=(6, 8), pady=8, sticky="nsew")

    def refresh_recent(self) -> None:
        self.recent_records.refresh()


class HomeStatusOverviewFrame(ctk.CTkFrame):
    """System status overview card."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        page_settings: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
            **kwargs,
        )
        self.gui = gui
        self.page_settings = page_settings
        self._build()

    def _build(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(
            inner,
            text="📊 系统状态",
            font=self.gui._get_font(14, "bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        ).pack(anchor="w", pady=(0, 10))

        info = getattr(self.gui, "_summarizer_info", {})
        avail = sum(1 for v in info.values() if v.available)
        total = len(info)
        s_color = ModernColors.SUCCESS if avail > 0 else ModernColors.ERROR
        self._stat_row(inner, "🤖 摘要器", f"{avail}/{total} 可用", s_color)

        exp = getattr(self.gui, "_exporter_info", {})
        e_avail = sum(1 for v in exp.values() if v.available)
        e_total = len(exp)
        e_color = ModernColors.SUCCESS if e_avail > 0 else ModernColors.ERROR
        self._stat_row(inner, "📤 导出器", f"{e_avail}/{e_total} 可用", e_color)

        cache_count = 0
        with contextlib.suppress(Exception):
            storage = self.gui.container.storage
            if storage:
                cache_count = storage.get_stats().total_entries
        self._stat_row(inner, "🗃️ 缓存", f"{cache_count} 条记录", ModernColors.INFO)

        settings_btn = ctk.CTkButton(
            inner,
            text="⚙️ 查看设置",
            font=self.gui._get_font(11),
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
            hover_color=(
                ModernColors.LIGHT_HOVER_SUBTLE,
                ModernColors.DARK_HOVER_SUBTLE,
            ),
            command=lambda: self.gui._show_page(self.page_settings),
        )
        settings_btn.pack(anchor="w", pady=(10, 0))

    def _stat_row(self, parent: Any, label: str, value: str, color: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)
        ctk.CTkLabel(
            row,
            text=label,
            font=self.gui._get_font(12),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
        ).pack(side="left")
        ctk.CTkLabel(
            row,
            text=value,
            font=self.gui._get_font(12, "bold"),
            text_color=color,
        ).pack(side="right")


class HomeRecentRecordsFrame(ctk.CTkFrame):
    """Recent processed articles card."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        page_history: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
            **kwargs,
        )
        self.gui = gui
        self.page_history = page_history
        self._recent_labels: list[Any] = []
        self._build()

    def _build(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            header,
            text="🕐 最近记录",
            font=self.gui._get_font(14, "bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="查看全部 →",
            font=self.gui._get_font(11),
            height=24,
            width=80,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(
                ModernColors.LIGHT_HOVER_SUBTLE,
                ModernColors.DARK_HOVER_SUBTLE,
            ),
            command=lambda: self.gui._show_page(self.page_history),
        ).pack(side="right")

        self._recent_container = inner
        self.refresh()

    def refresh(self) -> None:
        for lbl in self._recent_labels:
            with contextlib.suppress(Exception):
                lbl.destroy()
        self._recent_labels.clear()

        articles: list[Any] = []
        with contextlib.suppress(Exception):
            storage = self.gui.container.storage
            if storage:
                articles = storage.list_recent(limit=5)

        if not articles:
            empty = ctk.CTkLabel(
                self._recent_container,
                text="暂无记录，处理文章后将在此显示",
                font=self.gui._get_font(12),
                text_color=(
                    ModernColors.LIGHT_TEXT_MUTED,
                    ModernColors.DARK_TEXT_MUTED,
                ),
            )
            empty.pack(anchor="w", pady=8)
            self._recent_labels.append(empty)
            return

        for art in articles:
            row = ctk.CTkFrame(self._recent_container, fg_color="transparent")
            row.pack(fill="x", pady=2)
            self._recent_labels.append(row)

            title = getattr(art, "title", "无标题") or "无标题"
            if len(title) > 40:
                title = title[:38] + "…"
            ctk.CTkLabel(
                row,
                text=f"📄 {title}",
                font=self.gui._get_font(12),
                text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)

            author = getattr(art, "author", "") or ""
            if author:
                ctk.CTkLabel(
                    row,
                    text=author,
                    font=self.gui._get_font(10),
                    text_color=(
                        ModernColors.LIGHT_TEXT_MUTED,
                        ModernColors.DARK_TEXT_MUTED,
                    ),
                ).pack(side="right")
