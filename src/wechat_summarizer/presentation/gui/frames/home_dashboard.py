"""Home dashboard frame sections."""

from __future__ import annotations

import contextlib
import random
from collections.abc import Callable
from typing import Any

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..widgets.helpers import adjust_color_brightness

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

_TIPS = [
    ("📋", "粘贴即用", "复制微信文章链接，直接粘贴到下方输入框即可开始处理"),
    ("⌨️", "快捷键", "Ctrl+1~4 切换页面，Ctrl+D 切换主题，Ctrl+E 导出"),
    ("🤖", "AI 摘要", "在设置中配置 API 密钥，即可使用 DeepSeek/OpenAI 智能摘要"),
    ("📦", "批量打包", "批量处理后可一键导出为 ZIP 压缩包"),
    ("🗃️", "智能缓存", "已处理文章自动缓存，重复链接秒速加载"),
    ("📂", "文件导入", "在批量页面点击「从文件导入」支持 .txt 批量导入链接"),
]


class HomeWelcomeFrame(ctk.CTkFrame):
    """Welcome header and quick paste entry for the dashboard."""

    def __init__(self, master: Any, *, gui: Any, page_single: str, **kwargs: Any) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.page_single = page_single
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="👋 欢迎使用文章助手",
            font=self.gui._get_font(28, "bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        ).pack(anchor="w")

        ctk.CTkLabel(
            self,
            text="快速抓取、总结和导出微信公众号文章",
            font=self.gui._get_font(14),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
        ).pack(anchor="w", pady=(5, 12))

        paste_row = ctk.CTkFrame(
            self,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            corner_radius=Spacing.RADIUS_LG,
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        paste_row.pack(fill="x")

        inner = ctk.CTkFrame(paste_row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self.quick_entry = ctk.CTkEntry(
            inner,
            placeholder_text="粘贴微信文章链接，按 Enter 开始处理…",
            font=self.gui._get_font(13),
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        self.quick_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.quick_entry.bind("<Return>", self._on_quick_paste)

        go_btn = ctk.CTkButton(
            inner,
            text="开始 →",
            font=self.gui._get_font(13, "bold"),
            width=90,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(
                ModernColors.LIGHT_ACCENT_HOVER,
                ModernColors.DARK_ACCENT_HOVER,
            ),
            command=lambda: self._on_quick_paste(None),
        )
        go_btn.pack(side="right")

    def _on_quick_paste(self, _event: Any) -> None:
        url = self.quick_entry.get().strip()
        if not url:
            return

        self.gui._show_page(self.page_single)
        with contextlib.suppress(Exception):
            self.gui.url_entry.delete(0, "end")
            self.gui.url_entry.insert(0, url)
            self.quick_entry.delete(0, "end")


class HomeActionCardsFrame(ctk.CTkFrame):
    """Bento-style dashboard navigation cards."""

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
        self.grid_columnconfigure((0, 1, 2), weight=1)

        cards = [
            ("📄", "单篇处理", "抓取并生成摘要", self.pages["single"], ModernColors.INFO),
            ("📚", "批量处理", "多篇文章批量处理", self.pages["batch"], ModernColors.SUCCESS),
            ("📜", "历史记录", "查看已处理文章", self.pages["history"], ModernColors.WARNING),
        ]
        for i, (icon, title, desc, page, color) in enumerate(cards):
            card = self._create_animated_card(
                icon=icon,
                title=title,
                desc=desc,
                color=color,
                command=self._navigate_command(page),
            )
            card.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")

    def _navigate_command(self, page: str) -> Callable[[], None]:
        def navigate() -> None:
            self.gui._show_page(page)

        return navigate

    def _create_animated_card(
        self,
        *,
        icon: str,
        title: str,
        desc: str,
        color: str,
        command: Callable[[], None] | None = None,
    ) -> Any:
        card = ctk.CTkFrame(
            self,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )

        icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=36))
        icon_label.pack(pady=(24, 8))

        title_label = ctk.CTkLabel(
            card, text=title, font=self.gui._get_font(16, "bold"), text_color=color
        )
        title_label.pack()

        desc_label = ctk.CTkLabel(
            card,
            text=desc,
            font=self.gui._get_font(12),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
        )
        desc_label.pack(pady=(6, 16))

        btn = ctk.CTkButton(
            card,
            text="开始使用 →",
            font=self.gui._get_font(13),
            corner_radius=Spacing.RADIUS_MD,
            height=36,
            fg_color=color,
            hover_color=adjust_color_brightness(color, 1.15),
            command=command,
        )
        btn.pack(pady=(0, 24), padx=24, fill="x")

        def on_enter(_: Any) -> None:
            card.configure(
                fg_color=(ModernColors.LIGHT_CARD_HOVER, ModernColors.DARK_CARD_HOVER),
                border_color=(color, color),
            )
            title_label.configure(text_color=adjust_color_brightness(color, 1.2))

        def on_leave(_: Any) -> None:
            card.configure(
                fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
                border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
            )
            title_label.configure(text_color=color)

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        for widget in [icon_label, title_label, desc_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        return card


class HomeTipBarFrame(ctk.CTkFrame):
    """Compact random dashboard tip bar."""

    def __init__(self, master: Any, *, gui: Any, **kwargs: Any) -> None:
        super().__init__(
            master,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
            **kwargs,
        )
        self.gui = gui
        self._build()

    def _build(self) -> None:
        tip = random.choice(_TIPS)
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)

        ctk.CTkLabel(
            inner,
            text=f"{tip[0]}  {tip[1]}  ·  {tip[2]}",
            font=self.gui._get_font(12),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
            anchor="w",
        ).pack(fill="x")
