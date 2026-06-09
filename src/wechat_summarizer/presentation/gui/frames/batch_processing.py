"""Reusable frame sections for the batch-processing page."""

from __future__ import annotations

from collections.abc import Callable

from ..components.progress import LinearProgress
from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr
from .batch_export import BatchExportActionsFrame

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - GUI dependency is optional at runtime
    ctk = None  # type: ignore[assignment]


class BatchInputFrame(ctk.CTkFrame):
    """Left-side URL list and batch options panel."""

    def __init__(self, master, gui, stop_command, **kwargs):
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            **kwargs,
        )
        self.gui = gui
        self._stop_command = stop_command
        self.batch_url_text = None
        self.batch_url_status_label = None
        self.batch_method_var = None
        self.concurrency_var = None
        self.batch_start_btn = None
        self.batch_stop_btn = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=tr("🔗 URL列表"), font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 5)
        )

        ctk.CTkLabel(
            self,
            text=tr("每行输入一个URL，或从文件导入"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", padx=20)

        self.batch_url_text = ctk.CTkTextbox(
            self, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12)
        )
        self.batch_url_text.pack(fill="both", expand=True, padx=20, pady=(10, 5))

        self.batch_url_status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), anchor="w"
        )
        self.batch_url_status_label.pack(fill="x", padx=20, pady=(0, 5))

        self.batch_url_text.bind("<KeyRelease>", self.gui._on_batch_url_input_change)
        self.batch_url_text.bind("<FocusOut>", self.gui._on_batch_url_input_change)

        self._build_url_actions()
        self._build_options()
        self._build_processing_actions()

    def _build_url_actions(self) -> None:
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        import_btn = self.gui._create_modern_button(
            btn_frame,
            text=tr("📂 导入文件"),
            command=self.gui._on_import_urls,
            variant="ghost",
            size="small",
        )
        import_btn.pack(side="left", padx=(0, 5))

        paste_btn = self.gui._create_modern_button(
            btn_frame,
            text=tr("📋 粘贴"),
            command=self.gui._on_paste_urls,
            variant="ghost",
            size="small",
        )
        paste_btn.pack(side="left", padx=5)

        clear_btn = self.gui._create_modern_button(
            btn_frame,
            text=tr("🗑️ 清空"),
            command=lambda: self.batch_url_text.delete("1.0", "end"),
            variant="ghost",
            size="small",
        )
        clear_btn.pack(side="left", padx=5)

    def _build_options(self) -> None:
        options_frame = ctk.CTkFrame(self, fg_color="transparent")
        options_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(options_frame, text=tr("摘要方法:")).pack(side="left")

        available_methods = [
            name for name, info in self.gui._summarizer_info.items() if info.available
        ]
        if not available_methods:
            available_methods = ["simple"]

        self.batch_method_var = ctk.StringVar(value=available_methods[0])
        ctk.CTkOptionMenu(
            options_frame,
            values=available_methods,
            variable=self.batch_method_var,
            width=100,
            height=30,
        ).pack(side="left", padx=(10, 20))

        ctk.CTkLabel(options_frame, text=tr("并发数:")).pack(side="left")
        self.concurrency_var = ctk.StringVar(value="3")
        ctk.CTkEntry(options_frame, textvariable=self.concurrency_var, width=50, height=30).pack(
            side="left", padx=(10, 0)
        )

    def _build_processing_actions(self) -> None:
        start_stop_frame = ctk.CTkFrame(self, fg_color="transparent")
        start_stop_frame.pack(fill="x", padx=20, pady=(5, 20))

        self.batch_start_btn = self.gui._create_modern_button(
            start_stop_frame,
            text=tr("🚀 开始批量处理"),
            command=self.gui._on_batch_process,
            variant="primary",
            size="large",
        )
        self.batch_start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.batch_stop_btn = self.gui._create_modern_button(
            start_stop_frame,
            text=tr("⏹️ 停止"),
            command=self._stop_command,
            variant="danger",
            size="large",
        )
        self.batch_stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.batch_stop_btn.configure(state="disabled")


class BatchResultsFrame(ctk.CTkFrame):
    """Right-side batch results, progress, and export panel."""

    def __init__(self, master, gui, **kwargs):
        super().__init__(
            master,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            **kwargs,
        )
        self.gui = gui
        self.batch_result_frame = None
        self.batch_progress = None
        self.batch_status_label = None
        self.batch_elapsed_label = None
        self.batch_eta_label = None
        self.batch_rate_label = None
        self.batch_count_label = None
        self.batch_export_word_btn = None
        self.batch_export_md_btn = None
        self.batch_export_btn = None
        self.batch_export_html_btn = None
        self.export_actions_frame = None
        self._build()

    def _build(self) -> None:
        ctk.CTkLabel(self, text=tr("📋 处理结果"), font=ctk.CTkFont(size=14, weight="bold")).pack(
            anchor="w", padx=20, pady=(20, 10)
        )

        self.batch_result_frame = ctk.CTkScrollableFrame(self, corner_radius=Spacing.RADIUS_MD)
        self.batch_result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.batch_progress = LinearProgress(
            self, width=300, height=10, indeterminate=False, theme=self.gui._appearance_mode
        )
        self.batch_progress.pack(fill="x", padx=20, pady=5)
        self.batch_progress.set(0)

        self.batch_status_label = ctk.CTkLabel(
            self, text=tr("就绪"), font=ctk.CTkFont(size=12, weight="bold")
        )
        self.batch_status_label.pack(padx=20, pady=(0, 5))

        self._build_progress_detail()
        self._build_export_buttons()

    def _build_progress_detail(self) -> None:
        progress_detail_frame = ctk.CTkFrame(
            self,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
        )
        progress_detail_frame.pack(fill="x", padx=20, pady=(0, 10))

        detail_inner = ctk.CTkFrame(progress_detail_frame, fg_color="transparent")
        detail_inner.pack(fill="x", padx=15, pady=10)
        detail_inner.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.batch_elapsed_label = self._add_metric(
            detail_inner,
            column=0,
            title_factory=lambda: tr("⏱️ 已用时间"),
            value="00:00",
            color=ModernColors.INFO,
        )
        self.batch_eta_label = self._add_metric(
            detail_inner,
            column=1,
            title_factory=lambda: tr("⏳ 预计剩余"),
            value="--:--",
            color=ModernColors.WARNING,
        )
        self.batch_rate_label = self._add_metric(
            detail_inner,
            column=2,
            title_factory=lambda: tr("🚀 处理速率"),
            value=tr("0.00 篇/秒"),
            color=ModernColors.SUCCESS,
        )
        self.batch_count_label = self._add_metric(
            detail_inner,
            column=3,
            title_factory=lambda: tr("📊 成功/失败"),
            value="0 / 0",
            color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        )

    def _add_metric(
        self,
        parent,
        *,
        column: int,
        title_factory: Callable[[], str],
        value: str,
        color,
    ):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=column, sticky="nsew", padx=5)
        ctk.CTkLabel(
            frame,
            text=title_factory(),
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack()
        label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=color,
        )
        label.pack()
        return label

    def _build_export_buttons(self) -> None:
        self.export_actions_frame = BatchExportActionsFrame(
            self,
            gui=self.gui,
        )
        self.export_actions_frame.pack(fill="x", padx=20)
        self.batch_export_word_btn = self.export_actions_frame.batch_export_word_btn
        self.batch_export_md_btn = self.export_actions_frame.batch_export_md_btn
        self.batch_export_btn = self.export_actions_frame.batch_export_btn
        self.batch_export_html_btn = self.export_actions_frame.batch_export_html_btn


__all__ = ["BatchInputFrame", "BatchResultsFrame"]
