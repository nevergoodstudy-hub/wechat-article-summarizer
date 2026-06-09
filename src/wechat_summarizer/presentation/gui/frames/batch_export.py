"""Batch export action frame."""

from __future__ import annotations

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - GUI dependency is optional at runtime
    ctk = None  # type: ignore[assignment]


class BatchExportActionsFrame(ctk.CTkFrame):
    """Export buttons for processed batch results."""

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self.batch_export_word_btn = None
        self.batch_export_md_btn = None
        self.batch_export_btn = None
        self.batch_export_html_btn = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text=tr("📤 导出选项"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", pady=(5, 5))

        export_grid = ctk.CTkFrame(self, fg_color="transparent")
        export_grid.pack(fill="x", pady=(0, 20))
        export_grid.grid_columnconfigure(0, weight=1)
        export_grid.grid_columnconfigure(1, weight=1)

        self.batch_export_word_btn = ctk.CTkButton(
            export_grid,
            text=tr("📄 导出Word"),
            height=38,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.INFO,
            state="disabled",
            command=lambda: self.gui._on_batch_export_format("word"),
        )
        self.batch_export_word_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3), pady=(0, 5))

        self.batch_export_md_btn = ctk.CTkButton(
            export_grid,
            text=tr("📝 导出Markdown"),
            height=38,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.SUCCESS,
            state="disabled",
            command=lambda: self.gui._on_batch_export_format("markdown"),
        )
        self.batch_export_md_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0), pady=(0, 5))

        self.batch_export_btn = ctk.CTkButton(
            export_grid,
            text=tr("📦 压缩打包导出"),
            height=38,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.GRADIENT_MID,
            state="disabled",
            command=self.gui._on_batch_export,
        )
        self.batch_export_btn.grid(row=1, column=0, sticky="ew", padx=(0, 3), pady=(5, 0))

        self.batch_export_html_btn = ctk.CTkButton(
            export_grid,
            text=tr("🌐 导出HTML"),
            height=38,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.NEUTRAL_BTN_DISABLED,
            state="disabled",
            command=lambda: self.gui._on_batch_export_format("html"),
        )
        self.batch_export_html_btn.grid(row=1, column=1, sticky="ew", padx=(3, 0), pady=(5, 0))


__all__ = ["BatchExportActionsFrame"]
