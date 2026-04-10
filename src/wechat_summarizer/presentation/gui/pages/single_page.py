"""单篇处理页面

从 WechatSummarizerGUI 提取的单篇文章处理页面。
采用 CustomTkinter CTkFrame 子类化 + controller 模式。

2026 UI 增强:
- 剪贴板智能检测（自动识别微信链接）
- 摘要/要点复制按钮
- 处理中 skeleton 状态
"""

from __future__ import annotations

import contextlib
import re
from typing import TYPE_CHECKING

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

if TYPE_CHECKING:
    pass

_WECHAT_URL_RE = re.compile(r"https?://mp\.weixin\.qq\.com/s[/?]")


class SinglePage(ctk.CTkFrame):
    """单篇文章处理页面

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui

        # 公开属性 - 供外部通过别名访问
        self.url_entry = None
        self.url_status_label = None
        self.method_var = None
        self.method_menu = None
        self.summarize_var = None
        self.fetch_btn = None
        self.export_btn = None
        self.preview_text = None
        self.title_label = None
        self.author_label = None
        self.word_count_label = None
        self.summary_text = None
        self.points_text = None

        self._clipboard_banner: ctk.CTkFrame | None = None
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )
        self._build()

    # ==================================================================
    # 剪贴板智能检测
    # ==================================================================

    def on_page_shown(self) -> None:
        """页面显示时调用 - 检测剪贴板中的微信链接"""
        with contextlib.suppress(Exception):
            clip = self.clipboard_get().strip()
            if clip and _WECHAT_URL_RE.match(clip):
                current = self.url_entry.get().strip() if self.url_entry else ""
                if clip != current:
                    self._show_clipboard_banner(clip)

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """响应导航事件。"""
        _ = from_page
        if to_page == self.gui.PAGE_SINGLE:
            self.on_page_shown()

    def _show_clipboard_banner(self, url: str) -> None:
        """显示剪贴板智能提示横幅"""
        self._dismiss_clipboard_banner()
        banner = ctk.CTkFrame(
            self,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
        )
        # 插入到最顶部
        banner.pack(fill="x", pady=(0, 8), before=self.winfo_children()[0])

        inner = ctk.CTkFrame(banner, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)

        short = url if len(url) <= 50 else url[:48] + "…"
        ctk.CTkLabel(
            inner,
            text=f"📋 检测到剪贴板链接: {short}",
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            inner,
            text="粘贴使用",
            font=ctk.CTkFont(size=11, weight="bold"),
            width=80,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(
                ModernColors.LIGHT_ACCENT_HOVER,
                ModernColors.DARK_ACCENT_HOVER,
            ),
            command=lambda: self._apply_clipboard(url),
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            inner,
            text="✕",
            width=28,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            text_color=(
                ModernColors.LIGHT_TEXT_MUTED,
                ModernColors.DARK_TEXT_MUTED,
            ),
            hover_color=(
                ModernColors.LIGHT_HOVER_SUBTLE,
                ModernColors.DARK_HOVER_SUBTLE,
            ),
            command=self._dismiss_clipboard_banner,
        ).pack(side="right")

        self._clipboard_banner = banner

    def _apply_clipboard(self, url: str) -> None:
        """应用剪贴板链接"""
        if self.url_entry:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            with contextlib.suppress(Exception):
                self.gui._on_url_input_change()
        self._dismiss_clipboard_banner()

    def _dismiss_clipboard_banner(self) -> None:
        """关闭剪贴板横幅"""
        if self._clipboard_banner:
            with contextlib.suppress(Exception):
                self._clipboard_banner.destroy()
            self._clipboard_banner = None

    # ==================================================================
    # 复制辅助
    # ==================================================================

    def _copy_textbox(self, textbox: ctk.CTkTextbox, label: str = "内容") -> None:
        """复制 textbox 内容到剪贴板"""
        text = textbox.get("1.0", "end").strip()
        if not text:
            return
        with contextlib.suppress(Exception):
            self.clipboard_clear()
            self.clipboard_append(text)
        # toast 提示
        if hasattr(self.gui, "_toast_manager") and self.gui._toast_manager:
            self.gui._toast_manager.success(f"已复制{label}")

    def _build(self):
        """构建单篇处理页面"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(
            header, text=tr("📄 单篇文章处理"), font=ctk.CTkFont(size=24, weight="bold")
        ).pack(side="left")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # 左侧卡片 - 输入区
        left_card = ctk.CTkFrame(
            content,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
        )
        left_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        ctk.CTkLabel(
            left_card, text=tr("🔗 文章链接"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 8))

        # 使用现代化输入框组件 (2026 UI)
        self.url_entry = self.gui._create_modern_input(
            left_card, placeholder=tr("请输入微信公众号文章链接..."), show_clear_button=True
        )
        self.url_entry.pack(fill="x", padx=20)

        self.url_status_label = ctk.CTkLabel(
            left_card, text="", font=ctk.CTkFont(size=11), anchor="w"
        )
        self.url_status_label.pack(fill="x", padx=20, pady=(2, 0))

        self.url_entry.bind("<KeyRelease>", self.gui._on_url_input_change)
        self.url_entry.bind("<FocusOut>", self.gui._on_url_input_change)

        options_frame = ctk.CTkFrame(left_card, fg_color="transparent")
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

        btn_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        # 使用现代化按钮组件 (2026 UI)
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

        ctk.CTkLabel(
            left_card, text=tr("📄 内容预览"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(15, 8))

        self.preview_text = ctk.CTkTextbox(
            left_card, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12)
        )
        self.preview_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # 右侧卡片 - 结果区
        right_card = ctk.CTkFrame(
            content,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
        )
        right_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(
            right_card, text=tr("📰 文章信息"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        info_frame = ctk.CTkFrame(
            right_card, corner_radius=Spacing.RADIUS_MD, fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET)
        )
        info_frame.pack(fill="x", padx=20)

        self.title_label = ctk.CTkLabel(
            info_frame, text=f"{tr('标题')}: -", font=ctk.CTkFont(size=12), anchor="w"
        )
        self.title_label.pack(fill="x", padx=15, pady=(12, 4))

        self.author_label = ctk.CTkLabel(
            info_frame, text=f"{tr('公众号')}: -", font=ctk.CTkFont(size=12), anchor="w"
        )
        self.author_label.pack(fill="x", padx=15, pady=4)

        self.word_count_label = ctk.CTkLabel(
            info_frame, text=f"{tr('字数')}: -", font=ctk.CTkFont(size=12), anchor="w"
        )
        self.word_count_label.pack(fill="x", padx=15, pady=(4, 12))

        # 摘要区 - 带复制按钮
        summary_header = ctk.CTkFrame(right_card, fg_color="transparent")
        summary_header.pack(fill="x", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            summary_header, text=tr("📝 文章摘要"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            summary_header,
            text="📋 复制",
            width=60,
            height=24,
            corner_radius=Spacing.RADIUS_SM,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=lambda: self._copy_textbox(self.summary_text, "摘要"),
        ).pack(side="right")

        self.summary_text = ctk.CTkTextbox(
            right_card, height=150, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12)
        )
        self.summary_text.pack(fill="x", padx=20)

        # 关键要点区 - 带复制按钮
        points_header = ctk.CTkFrame(right_card, fg_color="transparent")
        points_header.pack(fill="x", padx=20, pady=(15, 8))

        ctk.CTkLabel(
            points_header, text=tr("📌 关键要点"), font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            points_header,
            text="📋 复制",
            width=60,
            height=24,
            corner_radius=Spacing.RADIUS_SM,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=lambda: self._copy_textbox(self.points_text, "要点"),
        ).pack(side="right")

        self.points_text = ctk.CTkTextbox(
            right_card, corner_radius=Spacing.RADIUS_MD, font=ctk.CTkFont(size=12)
        )
        self.points_text.pack(fill="both", expand=True, padx=20, pady=(0, 20))
