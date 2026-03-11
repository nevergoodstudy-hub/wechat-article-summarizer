"""URL 批量处理面板。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr
from .progress import LinearProgress

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

if TYPE_CHECKING:
    pass


class UrlBatchPanel(ctk.CTkFrame):
    """URL 批量文章处理面板。

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui

        # 公开属性 - 供外部通过别名访问
        self.batch_url_text = None
        self.batch_url_status_label = None
        self.batch_method_var = None
        self.concurrency_var = None
        self.batch_start_btn = None
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

        self._build()

    def _build(self):
        """构建 URL 批量处理界面"""
        ctk.CTkLabel(
            self, text=tr("📚 批量文章处理"), font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # 左侧卡片 - URL 输入
        left_card = ctk.CTkFrame(
            content,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
        )
        left_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            left_card, text=tr("🔗 URL列表"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        ctk.CTkLabel(
            left_card,
            text=tr("每行输入一个URL，或从文件导入"),
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", padx=20)

        self.batch_url_text = ctk.CTkTextbox(
            left_card, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12)
        )
        self.batch_url_text.pack(fill="both", expand=True, padx=20, pady=(10, 5))

        self.batch_url_status_label = ctk.CTkLabel(
            left_card, text="", font=ctk.CTkFont(size=11), anchor="w"
        )
        self.batch_url_status_label.pack(fill="x", padx=20, pady=(0, 5))

        self.batch_url_text.bind("<KeyRelease>", self.gui._on_batch_url_input_change)
        self.batch_url_text.bind("<FocusOut>", self.gui._on_batch_url_input_change)

        btn_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        # 使用现代化按钮组件 (2026 UI)
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

        options_frame = ctk.CTkFrame(left_card, fg_color="transparent")
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

        # 开始 / 停止 按钮容器
        start_stop_frame = ctk.CTkFrame(left_card, fg_color="transparent")
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
            command=self._on_stop_batch,
            variant="danger",
            size="large",
        )
        self.batch_stop_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.batch_stop_btn.configure(state="disabled")

        # 右侧卡片 - 结果区
        right_card = ctk.CTkFrame(
            content,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
        )
        right_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(
            right_card, text=tr("📋 处理结果"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.batch_result_frame = ctk.CTkScrollableFrame(
            right_card, corner_radius=Spacing.RADIUS_MD
        )
        self.batch_result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 使用现代化进度条组件 (2026 UI)
        self.batch_progress = LinearProgress(
            right_card, width=300, height=10, indeterminate=False, theme=self.gui._appearance_mode
        )
        self.batch_progress.pack(fill="x", padx=20, pady=5)
        self.batch_progress.set(0)

        self.batch_status_label = ctk.CTkLabel(
            right_card, text=tr("就绪"), font=ctk.CTkFont(size=12, weight="bold")
        )
        self.batch_status_label.pack(padx=20, pady=(0, 5))

        # 进度详情面板
        self._build_progress_detail(right_card)

        # 导出按钮区
        self._build_export_buttons(right_card)

    def _build_progress_detail(self, parent):
        """构建进度详情面板"""
        progress_detail_frame = ctk.CTkFrame(
            parent,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
        )
        progress_detail_frame.pack(fill="x", padx=20, pady=(0, 10))

        detail_inner = ctk.CTkFrame(progress_detail_frame, fg_color="transparent")
        detail_inner.pack(fill="x", padx=15, pady=10)
        detail_inner.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # 已用时间
        elapsed_frame = ctk.CTkFrame(detail_inner, fg_color="transparent")
        elapsed_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        ctk.CTkLabel(
            elapsed_frame,
            text=tr("⏱️ 已用时间"),
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack()
        self.batch_elapsed_label = ctk.CTkLabel(
            elapsed_frame,
            text="00:00",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.INFO,
        )
        self.batch_elapsed_label.pack()

        # 预计剩余
        eta_frame = ctk.CTkFrame(detail_inner, fg_color="transparent")
        eta_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        ctk.CTkLabel(
            eta_frame,
            text=tr("⏳ 预计剩余"),
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack()
        self.batch_eta_label = ctk.CTkLabel(
            eta_frame,
            text="--:--",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.WARNING,
        )
        self.batch_eta_label.pack()

        # 处理速率
        rate_frame = ctk.CTkFrame(detail_inner, fg_color="transparent")
        rate_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        ctk.CTkLabel(
            rate_frame,
            text=tr("🚀 处理速率"),
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack()
        self.batch_rate_label = ctk.CTkLabel(
            rate_frame,
            text=tr("0.00 篇/秒"),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=ModernColors.SUCCESS,
        )
        self.batch_rate_label.pack()

        # 成功/失败计数
        count_frame = ctk.CTkFrame(detail_inner, fg_color="transparent")
        count_frame.grid(row=0, column=3, sticky="nsew", padx=5)
        ctk.CTkLabel(
            count_frame,
            text=tr("📊 成功/失败"),
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack()
        self.batch_count_label = ctk.CTkLabel(
            count_frame,
            text="0 / 0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        )
        self.batch_count_label.pack()

    def _build_export_buttons(self, parent):
        """构建导出按钮区"""
        export_label = ctk.CTkLabel(
            parent,
            text=tr("📤 导出选项"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        )
        export_label.pack(anchor="w", padx=20, pady=(5, 5))

        # 使用 grid 布局确保所有按钮可见
        export_grid = ctk.CTkFrame(parent, fg_color="transparent")
        export_grid.pack(fill="x", padx=20, pady=(0, 20))
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

    def _on_stop_batch(self) -> None:
        """停止批量处理"""
        if hasattr(self.gui, "_batch_cancel_requested"):
            self.gui._batch_cancel_requested = True
        self.batch_stop_btn.configure(state="disabled")
        self.batch_status_label.configure(text=tr("正在停止…"))

    def set_processing_state(self, processing: bool) -> None:
        """切换开始/停止按钮状态"""
        if processing:
            self.batch_start_btn.configure(state="disabled")
            self.batch_stop_btn.configure(state="normal")
        else:
            self.batch_start_btn.configure(state="normal")
            self.batch_stop_btn.configure(state="disabled")
