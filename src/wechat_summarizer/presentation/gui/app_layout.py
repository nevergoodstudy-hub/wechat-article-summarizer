"""Main GUI shell layout assembly."""

from __future__ import annotations

from typing import Any

from loguru import logger

from .components.input import ModernInput
from .components.toast import init_toast_manager
from .ctk_compat import ctk
from .pages import BatchPage, HistoryPage, HomePage, SettingsPage, SinglePage
from .styles.colors import ModernColors
from .styles.spacing import Spacing
from .utils.i18n import tr
from .utils.performance import PerformanceMonitor
from .utils.responsive import Breakpoint, BreakpointManager, ResponsiveLayout
from .utils.shortcuts import KeyboardShortcutManager, Shortcut
from .widgets.helpers import adjust_color_brightness
from .widgets.log_panel import LogPanel
from .widgets.sidebar import Sidebar
from .widgets.tooltip import create_tooltip


class GUILayoutMixin:
    """Assemble the root shell, page frames, shortcuts, and responsive behavior."""

    def _build_ui(self: Any) -> None:
        self._perf_monitor = PerformanceMonitor()
        with self._perf_monitor.timer("gui_build_ui"):
            self.root.grid_columnconfigure(1, weight=1)
            self.root.grid_rowconfigure(0, weight=1)
            self._build_sidebar()
            self._build_main_content()

            self._toast_manager = init_toast_manager(
                self.root,
                position="top-right",
                theme=self._appearance_mode,
            )

            if not self._is_low_memory_mode():
                self._perf_monitor.start_monitoring(on_memory_warning=self._on_memory_warning)
                logger.debug("性能监控已启动")

            self._shortcut_manager = KeyboardShortcutManager(self.root)
            self._register_app_shortcuts()
            logger.debug("快捷键系统已初始化")

            self._breakpoint_manager = BreakpointManager(self.root)
            self._responsive_layout = ResponsiveLayout(self._breakpoint_manager)
            self._breakpoint_manager.on_breakpoint_change(self._on_breakpoint_change)
            logger.debug("响应式布局系统已初始化")

    def _on_memory_warning(self: Any, memory_mb: float) -> None:
        if memory_mb > 800:
            logger.warning(f"⚠️ 内存使用过高: {memory_mb:.1f} MB")
            if hasattr(self, "_toast_manager") and self._toast_manager:
                self._toast_manager.warning(
                    tr("内存使用过高: {memory_mb:.0f}MB").format(memory_mb=memory_mb)
                )

    def _on_breakpoint_change(
        self: Any,
        breakpoint: Breakpoint,
        width: int,
        height: int,
    ) -> None:
        logger.debug(f"响应式布局: 断点={breakpoint.value}, 尺寸={width}x{height}")

        if hasattr(self, "sidebar") and self.sidebar:
            if breakpoint == Breakpoint.XS:
                self.sidebar.configure(width=60)
            elif breakpoint == Breakpoint.SM:
                self.sidebar.configure(width=180)
            else:
                self.sidebar.configure(width=220)

    def _register_app_shortcuts(self: Any) -> None:
        shortcuts = [
            Shortcut(
                id="goto_home",
                name="跳转首页",
                keys="Ctrl+1",
                callback=lambda: self._show_page(self.PAGE_HOME),
                group=tr("导航"),
                description=tr("跳转到首页"),
            ),
            Shortcut(
                id="goto_single",
                name="跳转单篇处理",
                keys="Ctrl+2",
                callback=lambda: self._show_page(self.PAGE_SINGLE),
                group=tr("导航"),
                description=tr("跳转到单篇处理页面"),
            ),
            Shortcut(
                id="goto_batch",
                name="跳转批量处理",
                keys="Ctrl+3",
                callback=lambda: self._show_page(self.PAGE_BATCH),
                group=tr("导航"),
                description=tr("跳转到批量处理页面"),
            ),
            Shortcut(
                id="goto_history",
                name="跳转历史记录",
                keys="Ctrl+4",
                callback=lambda: self._show_page(self.PAGE_HISTORY),
                group=tr("导航"),
                description=tr("跳转到历史记录页面"),
            ),
            Shortcut(
                id="goto_settings",
                name="跳转设置",
                keys="Ctrl+,",
                callback=lambda: self._show_page(self.PAGE_SETTINGS),
                group=tr("导航"),
                description=tr("跳转到设置"),
            ),
            Shortcut(
                id="toggle_theme",
                name="切换主题",
                keys="Ctrl+D",
                callback=self._toggle_theme,
                group=tr("视图"),
                description=tr("切换深色/浅色主题"),
            ),
        ]

        for shortcut in shortcuts:
            self._shortcut_manager.register(shortcut)

    def _toggle_theme(self: Any) -> None:
        current = self.theme_switch.get()
        new_theme = "浅色" if current == "深色" else "深色"
        self.theme_switch.set(new_theme)
        self._on_theme_change(new_theme)

    def _create_modern_input(
        self: Any,
        master: Any,
        placeholder: str = "",
        label: str | None = None,
        show_clear_button: bool = True,
        **kwargs: Any,
    ) -> ModernInput:
        return ModernInput(
            master,
            placeholder=placeholder,
            label=label,
            show_clear_button=show_clear_button,
            theme=self._appearance_mode,
            **kwargs,
        )

    def _build_sidebar(self: Any) -> None:
        nav_items = [
            (self.PAGE_HOME, "🏠", "首页"),
            (self.PAGE_SINGLE, "📄", "单篇处理"),
            (self.PAGE_BATCH, "📚", "批量处理"),
            (self.PAGE_HISTORY, "📜", "历史记录"),
            (self.PAGE_SETTINGS, "⚙️", "设置"),
        ]
        self.sidebar = Sidebar(
            self.root,
            get_font=self._get_font,
            nav_items=nav_items,
            on_navigate=self._show_page_animated,
            on_theme_change=self._on_theme_change,
            summarizer_info=self._summarizer_info,
            exporter_info=self._exporter_info,
            container=self.container,
        )
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self._nav_buttons = self.sidebar.nav_buttons
        self.status_label = self.sidebar.status_label
        self.theme_switch = self.sidebar.theme_switch

    def _create_tooltip(self: Any, widget: Any, text: str) -> None:
        create_tooltip(widget, text, self._get_font)

    def _build_main_content(self: Any) -> None:
        self.main_container = ctk.CTkFrame(
            self.root,
            corner_radius=0,
            fg_color=(ModernColors.LIGHT_BG, ModernColors.DARK_BG),
        )
        self.main_container.grid(row=0, column=1, sticky="nswe")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=0)

        self.content_area = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_area.grid(row=0, column=0, sticky="nswe", padx=20, pady=(20, 10))
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self._build_home_page()
        self._build_single_page()
        self._build_batch_page()
        self._build_history_page()
        self._build_settings_page()
        self._build_log_panel()

    def _build_home_page(self: Any) -> None:
        self.home_page = HomePage(self.content_area, gui=self)
        self._page_frames[self.PAGE_HOME] = self.home_page

    def _build_single_page(self: Any) -> None:
        self.single_page = SinglePage(self.content_area, gui=self)
        self._page_frames[self.PAGE_SINGLE] = self.single_page

    def _build_batch_page(self: Any) -> None:
        self.batch_page = BatchPage(self.content_area, gui=self)
        self._page_frames[self.PAGE_BATCH] = self.batch_page

    def _build_history_page(self: Any) -> None:
        self.history_page = HistoryPage(self.content_area, gui=self)
        self._page_frames[self.PAGE_HISTORY] = self.history_page
        self.history_page.on_page_shown()

    def _build_settings_page(self: Any) -> None:
        self.settings_page = SettingsPage(self.content_area, gui=self)
        self._page_frames[self.PAGE_SETTINGS] = self.settings_page
        self.low_memory_var = self.settings_page.low_memory_var
        self.settings_page.update_summarizer_status_display()

    def _add_status_indicator(
        self: Any,
        parent: Any,
        label: str,
        value: str,
        is_ok: bool,
    ) -> None:
        frame = ctk.CTkFrame(
            parent,
            fg_color=(ModernColors.LIGHT_BG, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        frame.pack(side="left", padx=10, pady=5)

        inner_frame = ctk.CTkFrame(frame, fg_color="transparent")
        inner_frame.pack(padx=15, pady=10)

        color = ModernColors.SUCCESS if is_ok else ModernColors.ERROR
        hover_color = adjust_color_brightness(color, 1.2) if is_ok else ModernColors.ERROR

        status_label = ctk.CTkLabel(
            inner_frame,
            text=f"● {label}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=color,
        )
        status_label.pack(anchor="w")

        value_label = ctk.CTkLabel(
            inner_frame,
            text=value,
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        )
        value_label.pack(anchor="w")

        def on_enter(_: Any) -> None:
            frame.configure(
                fg_color=(ModernColors.LIGHT_CARD_HOVER, ModernColors.DARK_CARD_HOVER),
                border_color=(color, color),
            )
            status_label.configure(text_color=hover_color)

        def on_leave(_: Any) -> None:
            frame.configure(
                fg_color=(ModernColors.LIGHT_BG, ModernColors.DARK_SURFACE_ALT),
                border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
            )
            status_label.configure(text_color=color)

        frame.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        inner_frame.bind("<Enter>", on_enter)
        inner_frame.bind("<Leave>", on_leave)
        status_label.bind("<Enter>", on_enter)
        status_label.bind("<Leave>", on_leave)
        value_label.bind("<Enter>", on_enter)
        value_label.bind("<Leave>", on_leave)

    def _build_log_panel(self: Any) -> None:
        self.log_panel = LogPanel(
            self.main_container,
            get_font=self._get_font,
            root=self.root,
            on_status_change=self._set_status,
        )
        self.log_panel.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        self.log_text = self.log_panel.log_text
        self.log_toggle_btn = self.log_panel.log_toggle_btn
        self._log_expanded = True
