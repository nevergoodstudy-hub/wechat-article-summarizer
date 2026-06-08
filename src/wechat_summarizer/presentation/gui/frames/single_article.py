"""Reusable frame sections for the single-article page."""

from __future__ import annotations

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - GUI dependency is optional at runtime
    ctk = None  # type: ignore[assignment]


class SingleArticleInputFrame(ctk.CTkFrame):
    """Left-side article URL and preview panel."""

    def __init__(self, master, gui, **kwargs):
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            **kwargs,
        )
        self.gui = gui
        self.url_entry = None
        self.url_status_label = None
        self.method_var = None
        self.method_menu = None
        self.summarize_var = None
        self.fetch_btn = None
        self.export_btn = None
        self.preview_text = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=tr("🔗 文章链接"), font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 8)
        )

        self.url_entry = self.gui._create_modern_input(
            self,
            placeholder=tr("请输入微信公众号文章链接..."),
            show_clear_button=True,
        )
        self.url_entry.pack(fill="x", padx=20)

        self.url_status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), anchor="w")
        self.url_status_label.pack(fill="x", padx=20, pady=(2, 0))

        self.url_entry.bind("<KeyRelease>", self.gui._on_url_input_change)
        self.url_entry.bind("<FocusOut>", self.gui._on_url_input_change)

        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(options_frame, text=tr("摘要方法:"), font=ctk.CTkFont(size=13)).pack(
            side="left"
        )

        available_methods = [
            name for name, info in self.gui._summarizer_info.items() if info.available
        ]
        if not available_methods:
            available_methods = ["simple"]

        self.method_var = ctk.StringVar(value=available_methods[0])
        self.method_menu = ctk.CTkOptionMenu(
            options_frame,
            values=available_methods,
            variable=self.method_var,
            width=130,
            height=32,
            corner_radius=Spacing.RADIUS_MD,
            font=ctk.CTkFont(size=12),
        )
        self.method_menu.pack(side="left", padx=(10, 20))

        self.summarize_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame,
            text=tr("生成摘要"),
            variable=self.summarize_var,
            font=ctk.CTkFont(size=13),
            corner_radius=Spacing.RADIUS_SM,
        ).pack(side="left")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.fetch_btn = self.gui._create_modern_button(
            btn_frame,
            text=tr("🚀 开始处理"),
            command=self.gui._on_fetch,
            variant="primary",
            size="large",
        )
        self.fetch_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.export_btn = self.gui._create_modern_button(
            btn_frame,
            text=tr("📥 导出"),
            command=self.gui._on_export,
            variant="secondary",
            size="large",
        )
        self.export_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))
        self.export_btn.configure(state="disabled")

        ctk.CTkLabel(self, text=tr("📄 内容预览"), font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=20, pady=(15, 8)
        )

        self.preview_text = ctk.CTkTextbox(
            self,
            corner_radius=Spacing.RADIUS_MD,
            font=ctk.CTkFont(size=12),
        )
        self.preview_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))


class SingleArticleResultFrame(ctk.CTkFrame):
    """Right-side article metadata and generated summary panel."""

    def __init__(self, master, gui, copy_textbox, **kwargs):
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            **kwargs,
        )
        self.gui = gui
        self._copy_textbox = copy_textbox
        self.title_label = None
        self.author_label = None
        self.word_count_label = None
        self.summary_text = None
        self.points_text = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=tr("📰 文章信息"), font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        info_frame = ctk.CTkFrame(
            self,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
        )
        info_frame.pack(fill="x", padx=20)

        self.title_label = ctk.CTkLabel(
            info_frame,
            text=f"{tr('标题')}: -",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.title_label.pack(fill="x", padx=15, pady=(12, 4))

        self.author_label = ctk.CTkLabel(
            info_frame,
            text=f"{tr('公众号')}: -",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.author_label.pack(fill="x", padx=15, pady=4)

        self.word_count_label = ctk.CTkLabel(
            info_frame,
            text=f"{tr('字数')}: -",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.word_count_label.pack(fill="x", padx=15, pady=(4, 12))

        self._build_textbox_section("📝 文章摘要", "摘要", "summary_text", height=150)
        self._build_textbox_section("📌 关键要点", "要点", "points_text", height=None)

    def _build_textbox_section(
        self,
        title: str,
        copy_label: str,
        attr_name: str,
        *,
        height: int | None,
    ) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20 if attr_name == "summary_text" else 15, 8))

        ctk.CTkLabel(
            header,
            text=tr(title),
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="📋 复制",
            width=60,
            height=24,
            corner_radius=Spacing.RADIUS_SM,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=lambda: self._copy_textbox(getattr(self, attr_name), copy_label),
        ).pack(side="right")

        kwargs = {"corner_radius": Spacing.RADIUS_MD, "font": ctk.CTkFont(size=12)}
        if height is not None:
            kwargs["height"] = height
        textbox = ctk.CTkTextbox(self, **kwargs)
        if height is None:
            textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        else:
            textbox.pack(fill="x", padx=20)
        setattr(self, attr_name, textbox)


__all__ = ["SingleArticleInputFrame", "SingleArticleResultFrame"]
