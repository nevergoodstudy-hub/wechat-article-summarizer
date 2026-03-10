"""GUI主应用 - 现代化界面设计

采用CustomTkinter的现代sidebar导航布局：
- 左侧固定sidebar导航栏
- 深色/浅色主题支持
- 页面切换动画
- 日志面板
- Word导出预览
"""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import TYPE_CHECKING, Any

from loguru import logger

from ...bootstrap import AppRuntime, build_app_runtime
from ...shared.constants import GUI_MIN_SIZE, GUI_WINDOW_TITLE
from ...shared.progress import BatchProgressTracker, ProgressInfo

# 2026现代化GUI组件
from .components.button import ButtonSize, ButtonVariant, ModernButton
from .components.card import CardStyle, ModernCard, ShadowDepth
from .components.input import ModernInput
from .components.toast import init_toast_manager
from .dialogs.batch_archive_export import BatchArchiveExportDialog
from .dialogs.exit_confirm import ExitConfirmDialog
from .dialogs.word_preview import (
    build_content_preview_with_images,
    extract_images_from_article,
    show_batch_word_preview,
    show_word_preview,
)
from .event_bus import GUIEventBus
from .main_window import MainWindowCoordinator
from .pages import BatchPage, HistoryPage, HomePage, SettingsPage, SinglePage

# 2026现代化色彩系统
from .styles.colors import ModernColors
from .styles.spacing import Spacing
from .styles.typography import ChineseFonts
from .utils.i18n import set_language

# 性能监控与快捷键系统 (2026 UI)
from .utils.performance import PerformanceMonitor

# 响应式布局系统 (2026 UI)
from .utils.responsive import Breakpoint, BreakpointManager, ResponsiveLayout
from .utils.shortcuts import KeyboardShortcutManager, Shortcut
from .utils.windows_integration import Windows11StyleHelper
from .viewmodels import MainViewModel

# 提取的 GUI 组件（Phase 2 架构重构）
from .widgets.helpers import (
    LOW_MEMORY_THRESHOLD_GB,
    ExporterInfo,
    GUILogHandler,
    SummarizerInfo,
    UserPreferences,
    adjust_color_brightness,
    get_available_memory_gb,
)
from .widgets.log_panel import LogPanel
from .widgets.sidebar import Sidebar
from .widgets.splash_screen import SplashScreen
from .widgets.toast_notification import ToastNotification
from .widgets.tooltip import create_tooltip

if TYPE_CHECKING:
    from ...domain.entities import Article
    from ...infrastructure.config import AppSettings, Container
_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class WechatSummarizerGUI:
    """微信公众号文章总结器GUI - 现代化界面"""

    PAGE_HOME = "home"
    PAGE_SINGLE = "single"
    PAGE_BATCH = "batch"
    PAGE_HISTORY = "history"
    PAGE_SETTINGS = "settings"

    def __init__(self, container: Container, settings: AppSettings):
        if not _ctk_available:
            raise ImportError("customtkinter未安装，请运行: pip install customtkinter")
        else:
            # 基础初始化（不显示在进度条中）
            self.settings = settings
            self.user_prefs = UserPreferences()
            set_language(self.user_prefs.language)

            self._chinese_font = ChineseFonts.get_best_font()
            self._appearance_mode = "dark"
            ctk.set_appearance_mode(self._appearance_mode)
            ctk.set_default_color_theme("dark-blue")
            self.root = ctk.CTk()
            self.root.title(GUI_WINDOW_TITLE)
            self.root.geometry("1280x800")
            self.root.minsize(*GUI_MIN_SIZE)

            # 隐藏主窗口
            self.root.withdraw()

            # 创建启动画面
            splash = SplashScreen(self.root)

            # 注入的依赖
            self.container = container
            self.main_viewmodel: MainViewModel | None = None
            self.current_article: Article | None = None
            self.batch_urls: list[str] = []
            self.batch_results: list[Article] = []
            self._current_page = self.PAGE_HOME
            self._page_frames: dict[str, Any] = {}
            self._summarizer_info: dict[str, SummarizerInfo] = {}
            self._exporter_info: dict[str, ExporterInfo] = {}
            self._log_handler = None
            self._log_handler_id = None
            self._animation_running = False
            self._pulse_animation_id: str | None = None
            self._pulse_phase: int = 0

            # 任务运行状态跟踪（用于退出确认）
            self._batch_processing_active = False
            self._batch_export_active = False
            self._single_processing_active = False

            # 提示轮播组件状态
            self._tips_data: list[str] = []
            self._current_tip_index = 0
            self._tip_auto_switch_id = None
            self.event_bus = GUIEventBus()
            self._event_bus_subscriptions: list[Callable[[], None]] = []
            self._main_window = MainWindowCoordinator(self)
            self._bind_event_bus()

            # 定义启动任务列表
            # 权重根据任务实际耗时估算：
            # - 简单操作(内存操作)：权重 1
            # - 中等操作(文件/配置)：权重 2
            # - 耗时操作(网络请求)：权重 4-5

            def task_apply_window_style():
                """应用窗口样式"""
                Windows11StyleHelper.apply_window_style(self.root, self._appearance_mode)

            def task_init_container():
                """初始化依赖注入容器"""
                # Container 已通过参数注入，加载用户偏好中的 API 密钥
                saved_api_keys = self.user_prefs.get_all_api_keys()
                if any(saved_api_keys.values()):
                    self.container.reload_summarizers(saved_api_keys)
                # 创建主视图模型（MVVM 架构）
                self.main_viewmodel = MainViewModel(self.container)

            def task_detect_summarizers():
                """检测可用的摘要服务"""
                self._summarizer_info = self._get_summarizer_info()

            def task_detect_exporters():
                """检测可用的导出器"""
                self._exporter_info = self._get_exporter_info()

            def task_build_ui():
                """构建用户界面"""
                self._build_ui()

            def task_setup_logging():
                """设置日志处理器"""
                self._setup_log_handler()

            def task_init_system():
                """初始化系统设置"""
                self._init_system_settings()

            def task_show_home():
                """显示主页"""
                self._show_page(self.PAGE_HOME)

            # 注册任务（名称, 权重, 函数, 详细描述）
            splash.add_task("正在应用窗口样式", 1, task_apply_window_style, "配置 Windows 11 风格")
            splash.add_task("正在初始化容器", 2, task_init_container, "加载依赖注入框架")
            splash.add_task(
                "正在检测摘要服务", 5, task_detect_summarizers, "检测 Ollama、OpenAI 等服务状态"
            )
            splash.add_task("正在检测导出器", 2, task_detect_exporters, "检测 Word、PDF 导出支持")
            splash.add_task("正在构建用户界面", 4, task_build_ui, "创建页面和控件")
            splash.add_task("正在配置日志系统", 1, task_setup_logging, "设置日志输出")
            splash.add_task("正在初始化系统", 2, task_init_system, "加载用户偏好设置")
            splash.add_task("正在准备主页", 1, task_show_home, "切换到主页视图")

            # 显示启动画面并执行任务
            splash.show()
            success = splash.run_tasks()

            if success:
                splash.set_complete("启动完成！")
            else:
                splash.set_complete("启动完成（部分服务不可用）")

            # 关闭启动画面，显示主窗口
            splash.close(delay_ms=400)
            self.root.after(450, self._show_main_window)

            self._check_memory_on_startup()

    def _show_main_window(self):
        """显示主窗口并播放欢迎动画"""
        self._get_main_window_coordinator().show_main_window()

    def _check_memory_on_startup(self):
        """启动时检测内存，如果低于阈值则提示用户"""
        if self.user_prefs.low_memory_mode or self.user_prefs.low_memory_prompt_dismissed:
            return
        available_gb = get_available_memory_gb()
        if available_gb is None:
            logger.debug("无法检测系统内存（psutil 未安装）")
            return
        logger.info(f"系统可用内存: {available_gb:.2f} GB")
        if available_gb < LOW_MEMORY_THRESHOLD_GB:
            self.root.after(1500, lambda: self._show_low_memory_warning(available_gb))

    def _show_low_memory_warning(self, available_gb: float):
        """显示低内存警告弹窗"""

        def on_enable():
            self.user_prefs.low_memory_mode = True
            if hasattr(self, "low_memory_var"):
                self.low_memory_var.set(True)
            self._apply_low_memory_optimizations()
            logger.info("✅ 已启用低内存模式")
            # 使用新ToastManager (2026 UI组件)
            if hasattr(self, "_toast_manager") and self._toast_manager:
                self._toast_manager.success("已启用低内存模式，应用将减少内存占用")
            else:
                ToastNotification(
                    self.root,
                    "低内存模式",
                    "已启用低内存模式，应用将减少内存占用",
                    toast_type="success",
                    duration_ms=3000,
                )

        def on_dismiss():
            self.user_prefs.low_memory_prompt_dismissed = True
            logger.info("用户选择忽略低内存提示")

        ToastNotification(
            self.root,
            "⚠️ 内存不足",
            f"检测到系统可用内存仅 {available_gb:.1f} GB（低于 {LOW_MEMORY_THRESHOLD_GB:.0f} GB）\n\n建议启用「低内存模式」以获得更好的体验。",
            toast_type="warning",
            duration_ms=0,
            show_buttons=True,
            on_confirm=on_enable,
            on_cancel=on_dismiss,
        )

    def _get_main_window_coordinator(self) -> MainWindowCoordinator:
        """获取主窗口协调器。"""
        coordinator = getattr(self, "_main_window", None)
        if coordinator is None:
            coordinator = MainWindowCoordinator(self)
            self._main_window = coordinator
        return coordinator

    def _apply_low_memory_optimizations(self):
        """应用低内存模式优化"""
        # 1. 减少日志缓存行数
        if hasattr(self, "_log_handler") and self._log_handler:
            self._log_handler.set_low_memory_mode(True)
        # 2. 禁用动画效果
        self._animation_running = False
        # 3. 记录低内存模式状态，供其他组件检查
        self._low_memory_mode_active = True
        logger.debug("已应用低内存优化：减少日志缓存 (200行)、禁用动画效果")

    def _is_low_memory_mode(self) -> bool:
        """检查是否处于低内存模式"""
        return getattr(self, "_low_memory_mode_active", False) or self.user_prefs.low_memory_mode

    def _get_font(self, size: int = 14, weight: str = "normal") -> ctk.CTkFont:
        """获取配置好的中文字体"""
        return ctk.CTkFont(family=self._chinese_font, size=size, weight=weight)

    def _create_modern_button(
        self,
        master,
        text: str,
        command=None,
        variant: str = "primary",
        size: str = "medium",
        **kwargs,
    ):
        """创建现代化按钮 (2026 UI设计)

        Args:
            master: 父容器
            text: 按钮文本
            command: 点击回调
            variant: 按钮变体 ("primary", "secondary", "ghost", "danger")
            size: 按钮尺寸 ("small", "medium", "large")
            **kwargs: 其他参数

        Returns:
            ModernButton: 现代化按钮实例
        """
        # 映射变体字符串到枚举
        variant_map = {
            "primary": ButtonVariant.PRIMARY,
            "secondary": ButtonVariant.SECONDARY,
            "ghost": ButtonVariant.GHOST,
            "danger": ButtonVariant.DANGER,
            "text": ButtonVariant.TEXT,
        }
        size_map = {
            "small": ButtonSize.SMALL,
            "medium": ButtonSize.MEDIUM,
            "large": ButtonSize.LARGE,
        }

        return ModernButton(
            master,
            text=text,
            command=command,
            variant=variant_map.get(variant, ButtonVariant.PRIMARY),
            size=size_map.get(size, ButtonSize.MEDIUM),
            theme=self._appearance_mode,
            **kwargs,
        )

    def _create_modern_card(
        self, master, width: int = 300, height: int = 200, style: str = "elevated", **kwargs
    ):
        """创建现代化卡片 (2026 UI设计)

        Args:
            master: 父容器
            width: 宽度
            height: 高度
            style: 卡片样式 ("solid", "outlined", "elevated", "glass")
            **kwargs: 其他参数

        Returns:
            ModernCard: 现代化卡片实例
        """
        from .components.card import CornerRadius

        style_map = {
            "solid": CardStyle.SOLID,
            "outlined": CardStyle.OUTLINED,
            "elevated": CardStyle.ELEVATED,
            "glass": CardStyle.GLASS,
        }

        return ModernCard(
            master,
            width=width,
            height=height,
            corner_radius=CornerRadius.MEDIUM,
            shadow_depth=ShadowDepth.MEDIUM,
            style=style_map.get(style, CardStyle.ELEVATED),
            theme=self._appearance_mode,
            **kwargs,
        )

    def _play_welcome_animation(self):
        """播放欢迎动画"""
        self._set_status("欢迎使用！", ModernColors.SUCCESS)

    def _get_summarizer_info(self) -> dict[str, SummarizerInfo]:
        """获取摘要器可用性信息"""
        info = {}
        info["simple"] = SummarizerInfo("simple", True, "基于规则的简单摘要")
        info["textrank"] = SummarizerInfo("textrank", True, "基于图算法的抽取式摘要")
        ollama_available = True
        ollama_reason = ""
        try:
            import httpx

            with httpx.Client(timeout=2) as client:
                client.get(f"{self.settings.ollama.host}/api/tags")
            ollama_reason = "本地Ollama服务"
        except Exception:
            ollama_available = False
            ollama_reason = f"无法连接到 {self.settings.ollama.host}"
        info["ollama"] = SummarizerInfo("ollama", ollama_available, ollama_reason)
        openai_key = (
            self.user_prefs.get_api_key("openai") or self.settings.openai.api_key.get_secret_value()
        )
        if openai_key:
            info["openai"] = SummarizerInfo("openai", True, "OpenAI GPT")
        else:
            info["openai"] = SummarizerInfo("openai", False, "需要配置 API Key")
        # DeepSeek - 国产高性能大模型
        deepseek_key = (
            self.user_prefs.get_api_key("deepseek")
            or self.settings.deepseek.api_key.get_secret_value()
        )
        if deepseek_key:
            info["deepseek"] = SummarizerInfo("deepseek", True, "DeepSeek V3")
        else:
            info["deepseek"] = SummarizerInfo("deepseek", False, "需要配置 API Key")
        anthropic_key = (
            self.user_prefs.get_api_key("anthropic")
            or self.settings.anthropic.api_key.get_secret_value()
        )
        if anthropic_key:
            info["anthropic"] = SummarizerInfo("anthropic", True, "Claude AI")
        else:
            info["anthropic"] = SummarizerInfo("anthropic", False, "需要配置 API Key")
        zhipu_key = (
            self.user_prefs.get_api_key("zhipu") or self.settings.zhipu.api_key.get_secret_value()
        )
        if zhipu_key:
            info["zhipu"] = SummarizerInfo("zhipu", True, "智谱AI GLM")
        else:
            info["zhipu"] = SummarizerInfo("zhipu", False, "需要配置 API Key")
        return info

    def _get_exporter_info(self) -> dict[str, ExporterInfo]:
        """获取导出器可用性信息"""
        info = {}
        info["html"] = ExporterInfo("html", True)
        info["markdown"] = ExporterInfo("markdown", True)
        info["zip"] = ExporterInfo("zip", True)
        try:
            import docx  # noqa: F401

            info["word"] = ExporterInfo("word", True)
        except ImportError:
            info["word"] = ExporterInfo("word", False, "缺少 python-docx")
        return info

    def _setup_log_handler(self):
        """设置日志Handler"""
        if hasattr(self, "log_text") and self.log_text:
            self._log_handler = GUILogHandler(
                self.log_text, self.root, low_memory_mode=self.user_prefs.low_memory_mode
            )
            self._log_handler_id = logger.add(
                self._log_handler.write,
                format="{time:HH:mm:ss} | {level:<8} | {message}",
                level="DEBUG",
                colorize=False,
            )
            logger.info("🚀 应用已启动")
            # 如果已启用低内存模式，应用优化
            if self.user_prefs.low_memory_mode:
                self._apply_low_memory_optimizations()
                logger.info("📦 低内存模式已启用")

    def _init_system_settings(self):
        """初始化系统设置"""
        # 始终设置窗口关闭事件处理器（处理退出确认）
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        if self.user_prefs.minimize_to_tray:
            logger.debug("已启用最小化到系统托盘")
        self._sync_autostart_status()

    def _sync_autostart_status(self):
        """同步开机自启动状态（检查实际快捷方式是否存在）"""
        startup_folder = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )
        shortcut_path = startup_folder / "微信文章总结器.lnk"
        actual_enabled = shortcut_path.exists()
        if self.user_prefs.auto_start_enabled != actual_enabled:
            self.user_prefs.auto_start_enabled = actual_enabled
            logger.debug(f"开机自启动状态已同步: {('enabled' if actual_enabled else 'disabled')}")

    def _bind_event_bus(self) -> None:
        """绑定主窗口级事件总线订阅。"""
        self._event_bus_subscriptions.append(self._get_main_window_coordinator().bind_event_bus())

    def _clear_event_bus_subscriptions(self) -> None:
        """清理事件总线订阅。"""
        for unsubscribe in getattr(self, "_event_bus_subscriptions", []):
            with contextlib.suppress(Exception):
                unsubscribe()
        if hasattr(self, "_event_bus_subscriptions"):
            self._event_bus_subscriptions.clear()
        if hasattr(self, "event_bus"):
            self.event_bus.clear()

    def _publish_navigation(self, page_id: str, *, animated: bool = False) -> None:
        """发布页面切换事件。"""
        self.event_bus.publish("navigate", page_id=page_id, animated=animated)

    def _handle_navigation_event(
        self,
        page_id: str,
        animated: bool = False,
        **_: Any,
    ) -> None:
        """处理组件发出的导航事件。"""
        self._get_main_window_coordinator().handle_navigation_event(
            page_id,
            animated=animated,
        )

    def _build_ui(self):
        """构建用户界面"""
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_main_content()

        # 初始化全局Toast管理器 (2026 UI组件)
        self._toast_manager = init_toast_manager(
            self.root, position="top-right", theme=self._appearance_mode
        )

        # 初始化性能监控 (2026 UI组件)
        self._perf_monitor = PerformanceMonitor()
        if not self._is_low_memory_mode():
            # 仅在非低内存模式下启用性能监控
            self._perf_monitor.start_monitoring(on_memory_warning=self._on_memory_warning)
            logger.debug("性能监控已启动")

        # 初始化快捷键系统 (2026 UI组件)
        self._shortcut_manager = KeyboardShortcutManager(self.root)
        self._register_app_shortcuts()
        logger.debug("快捷键系统已初始化")

        # 初始化响应式布局系统 (2026 UI组件)
        self._breakpoint_manager = BreakpointManager(self.root)
        self._responsive_layout = ResponsiveLayout(self._breakpoint_manager)
        self._breakpoint_manager.on_breakpoint_change(self._on_breakpoint_change)
        logger.debug("响应式布局系统已初始化")

    def _on_memory_warning(self, memory_mb: float):
        """内存警告回调"""
        if memory_mb > 800:
            logger.warning(f"⚠️ 内存使用过高: {memory_mb:.1f} MB")
            if hasattr(self, "_toast_manager") and self._toast_manager:
                self._toast_manager.warning(f"内存使用过高: {memory_mb:.0f}MB")

    def _on_breakpoint_change(self, breakpoint: Breakpoint, width: int, height: int):
        """响应式布局断点变化回调 (2026 UI)

        根据窗口大小调整布局：
        - XS (<768px): 紧凑布局，隐藏部分元素
        - SM (768-1024px): 平板布局
        - MD (1024-1440px): 标准布局
        - LG (1440-1920px): 桌面布局
        - XL (>1920px): 宽屏布局

        Args:
            breakpoint: 当前断点
            width: 窗口宽度
            height: 窗口高度
        """
        logger.debug(f"响应式布局: 断点={breakpoint.value}, 尺寸={width}x{height}")

        # 根据断点调整侧边栏宽度
        if hasattr(self, "sidebar") and self.sidebar:
            if breakpoint == Breakpoint.XS:
                # 移动端：隐藏侧边栏文字，只显示图标
                self.sidebar.configure(width=60)
            elif breakpoint == Breakpoint.SM:
                # 平板：稍窄侧边栏
                self.sidebar.configure(width=180)
            else:
                # 桌面：标准宽度
                self.sidebar.configure(width=220)

    def _register_app_shortcuts(self):
        """注册应用程序快捷键"""
        shortcuts = [
            Shortcut(
                id="goto_home",
                name="跳转首页",
                keys="Ctrl+1",
                callback=lambda: self._publish_navigation(self.PAGE_HOME),
                group="导航",
                description="跳转到首页",
            ),
            Shortcut(
                id="goto_single",
                name="跳转单篇处理",
                keys="Ctrl+2",
                callback=lambda: self._publish_navigation(self.PAGE_SINGLE),
                group="导航",
                description="跳转到单篇处理页面",
            ),
            Shortcut(
                id="goto_batch",
                name="跳转批量处理",
                keys="Ctrl+3",
                callback=lambda: self._publish_navigation(self.PAGE_BATCH),
                group="导航",
                description="跳转到批量处理页面",
            ),
            Shortcut(
                id="goto_history",
                name="跳转历史记录",
                keys="Ctrl+4",
                callback=lambda: self._publish_navigation(self.PAGE_HISTORY),
                group="导航",
                description="跳转到历史记录页面",
            ),
            Shortcut(
                id="goto_settings",
                name="跳转设置",
                keys="Ctrl+,",
                callback=lambda: self._publish_navigation(self.PAGE_SETTINGS),
                group="导航",
                description="跳转到设置页面",
            ),
            Shortcut(
                id="toggle_theme",
                name="切换主题",
                keys="Ctrl+D",
                callback=self._toggle_theme,
                group="视图",
                description="切换深色/浅色主题",
            ),
        ]

        for shortcut in shortcuts:
            self._shortcut_manager.register(shortcut)

    def _toggle_theme(self):
        """切换主题"""
        current = self.theme_switch.get()
        new_theme = "浅色" if current == "深色" else "深色"
        self.theme_switch.set(new_theme)
        self._on_theme_change(new_theme)

    def _create_modern_input(
        self,
        master,
        placeholder: str = "",
        label: str | None = None,
        show_clear_button: bool = True,
        **kwargs,
    ):
        """创建现代化输入框 (2026 UI设计)

        Args:
            master: 父容器
            placeholder: 占位符文本
            label: 浮动标签文本
            show_clear_button: 是否显示清除按钮
            **kwargs: 其他参数

        Returns:
            ModernInput: 现代化输入框实例
        """
        return ModernInput(
            master,
            placeholder=placeholder,
            label=label,
            show_clear_button=show_clear_button,
            theme=self._appearance_mode,
            **kwargs,
        )

    def _build_sidebar(self):
        """构建左侧导航栏 - 委托给 Sidebar 组件"""
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
            event_bus=self.event_bus,
            on_theme_change=self._on_theme_change,
            summarizer_info=self._summarizer_info,
            exporter_info=self._exporter_info,
            container=self.container,
        )
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        # 向后兼容的属性别名
        self._nav_buttons = self.sidebar.nav_buttons
        self.status_label = self.sidebar.status_label
        self.theme_switch = self.sidebar.theme_switch

    def _create_tooltip(self, widget, text: str):
        """创建工具提示 - 委托给 create_tooltip 函数"""
        create_tooltip(widget, text, self._get_font)

    def _build_main_content(self):
        """构建主内容区"""
        self.main_container = ctk.CTkFrame(
            self.root, corner_radius=0, fg_color=(ModernColors.LIGHT_BG, ModernColors.DARK_BG)
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

    def _build_home_page(self):
        """构建首页 - 委托给 HomePage 组件"""
        self.home_page = HomePage(self.content_area, gui=self)
        self._page_frames[self.PAGE_HOME] = self.home_page

    def _build_single_page(self):
        """构建单篇处理页面 - 委托给 SinglePage 组件"""
        self.single_page = SinglePage(self.content_area, gui=self)
        self._page_frames[self.PAGE_SINGLE] = self.single_page
        # 向后兼容的属性别名
        self.url_entry = self.single_page.url_entry
        self.url_status_label = self.single_page.url_status_label
        self.method_var = self.single_page.method_var
        self.method_menu = self.single_page.method_menu
        self.summarize_var = self.single_page.summarize_var
        self.fetch_btn = self.single_page.fetch_btn
        self.export_btn = self.single_page.export_btn
        self.preview_text = self.single_page.preview_text
        self.title_label = self.single_page.title_label
        self.author_label = self.single_page.author_label
        self.word_count_label = self.single_page.word_count_label
        self.summary_text = self.single_page.summary_text
        self.points_text = self.single_page.points_text

    def _build_batch_page(self):
        """构建批量处理页面 - 委托给 BatchPage 组件"""
        self.batch_page = BatchPage(self.content_area, gui=self)
        self._page_frames[self.PAGE_BATCH] = self.batch_page
        # 向后兼容的属性别名
        self.batch_url_text = self.batch_page.batch_url_text
        self.batch_url_status_label = self.batch_page.batch_url_status_label
        self.batch_method_var = self.batch_page.batch_method_var
        self.concurrency_var = self.batch_page.concurrency_var
        self.batch_start_btn = self.batch_page.batch_start_btn
        self.batch_result_frame = self.batch_page.batch_result_frame
        self.batch_progress = self.batch_page.batch_progress
        self.batch_status_label = self.batch_page.batch_status_label
        self.batch_elapsed_label = self.batch_page.batch_elapsed_label
        self.batch_eta_label = self.batch_page.batch_eta_label
        self.batch_rate_label = self.batch_page.batch_rate_label
        self.batch_count_label = self.batch_page.batch_count_label
        self.batch_export_word_btn = self.batch_page.batch_export_word_btn
        self.batch_export_md_btn = self.batch_page.batch_export_md_btn
        self.batch_export_btn = self.batch_page.batch_export_btn
        self.batch_export_html_btn = self.batch_page.batch_export_html_btn

    def _build_history_page(self):
        """构建历史记录页面 - 委托给 HistoryPage 组件"""
        self.history_page = HistoryPage(self.content_area, gui=self)
        self._page_frames[self.PAGE_HISTORY] = self.history_page
        # 向后兼容的属性别名
        self.cache_stats_label = self.history_page.cache_stats_label
        self.history_frame = self.history_page.history_frame
        # 刷新历史记录（必须在 history_frame 别名设置之后调用）
        self.history_page._refresh_history()

    def _build_settings_page(self):
        """构建设置页面 - 委托给 SettingsPage 组件"""
        self.settings_page = SettingsPage(self.content_area, gui=self)
        self._page_frames[self.PAGE_SETTINGS] = self.settings_page
        # 向后兼容的属性别名
        self.summarizer_status_frame = self.settings_page.summarizer_status_frame
        self._api_key_entries = self.settings_page._api_key_entries
        self._openai_show_var = self.settings_page._openai_show_var
        self._deepseek_show_var = self.settings_page._deepseek_show_var
        self._anthropic_show_var = self.settings_page._anthropic_show_var
        self._zhipu_show_var = self.settings_page._zhipu_show_var
        self.api_status_label = self.settings_page.api_status_label
        self.export_dir_entry = self.settings_page.export_dir_entry
        self.remember_dir_var = self.settings_page.remember_dir_var
        self.default_format_var = self.settings_page.default_format_var
        self.autostart_var = self.settings_page.autostart_var
        self.minimize_tray_var = self.settings_page.minimize_tray_var
        self.low_memory_var = self.settings_page.low_memory_var
        self.language_var = self.settings_page.language_var
        self.settings_status_label = self.settings_page.settings_status_label
        self.memory_status_label = self.settings_page.memory_status_label
        # 初始化摘要器状态显示（必须在别名设置之后调用）
        self.settings_page.update_summarizer_status_display()

    def _add_status_indicator(self, parent, label: str, value: str, is_ok: bool):
        """添加状态指示器 - 带悬停动画效果"""
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

        def on_enter(e):
            frame.configure(
                fg_color=(ModernColors.LIGHT_CARD_HOVER, ModernColors.DARK_CARD_HOVER),
                border_color=(color, color),
            )
            status_label.configure(text_color=hover_color)

        def on_leave(e):
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

    def _on_window_close(self):
        """窗口关闭事件处理器 - 统一处理退出逻辑

        处理以下场景：
        1. 有正在运行的任务 -> 显示确认对话框
        2. 无任务 + 已启用托盘 -> 最小化到托盘
        3. 无任务 + 未启用托盘 -> 直接退出
        """
        # 检查是否有正在运行的任务
        active_task = self._get_active_task_info()

        if active_task:
            # 有任务正在运行，显示确认对话框
            dialog = ExitConfirmDialog(
                self.root,
                title="任务正在进行中",
                message="当前有任务正在运行，确定要退出吗？",
                task_info=active_task,
                icon="warning",
            )

            result = dialog.get()

            if result == "exit":
                # 用户选择强制退出
                logger.warning(f"用户强制退出，中断任务: {active_task}")
                self._force_exit()
            elif result == "minimize":
                # 用户选择最小化到后台
                logger.info("用户选择后台运行")
                self._on_close_to_tray()
            else:
                # 用户取消，继续任务
                logger.debug("用户取消退出，继续任务")
        else:
            # 没有任务运行
            if self.user_prefs.minimize_to_tray:
                # 最小化到托盘
                self._on_close_to_tray()
            else:
                # 直接退出
                self._safe_exit()

    def _get_active_task_info(self) -> str | None:
        """获取当前运行中的任务信息

        Returns:
            任务描述字符串，如果没有任务则返回 None
        """
        tasks = []

        # 检查批量处理状态
        if self._batch_processing_active:
            if hasattr(self, "_batch_progress_tracker") and self._batch_progress_tracker:
                tracker = self._batch_progress_tracker
                tasks.append(f"批量处理 ({tracker.current}/{tracker.total} 篇)")
            else:
                tasks.append("批量处理中")

        # 检查批量导出状态
        if self._batch_export_active:
            if hasattr(self, "_export_progress_tracker") and self._export_progress_tracker:
                tracker = self._export_progress_tracker
                tasks.append(f"批量导出 ({tracker.current}/{tracker.total} 篇)")
            elif hasattr(self, "_zip_progress_tracker") and self._zip_progress_tracker:
                tracker = self._zip_progress_tracker
                tasks.append(f"ZIP打包 ({tracker.current}/{tracker.total} 篇)")
            else:
                tasks.append("批量导出中")

        # 检查单篇处理状态
        if self._single_processing_active:
            tasks.append("单篇文章处理中")

        if tasks:
            return " | ".join(tasks)
        return None

    def _force_exit(self):
        """强制退出应用（不等待任务完成）"""
        try:
            # 释放日志资源
            if self._log_handler_id:
                with contextlib.suppress(Exception):
                    logger.remove(self._log_handler_id)
            self._clear_event_bus_subscriptions()

            # 关闭窗口
            self.root.destroy()
        except Exception as e:
            logger.error(f"强制退出时出错: {e}")
            self.root.destroy()

    def _safe_exit(self):
        """安全退出应用（无任务运行时的正常退出）"""
        try:
            # 释放日志资源
            if self._log_handler_id:
                with contextlib.suppress(Exception):
                    logger.remove(self._log_handler_id)
            self._clear_event_bus_subscriptions()

            logger.info("应用正常退出")
            self.root.destroy()
        except Exception as e:
            logger.error(f"安全退出时出错: {e}")
            self.root.destroy()

    def _on_close_to_tray(self):
        """关闭窗口时最小化到托盘"""
        self.root.withdraw()
        logger.info("窗口已最小化到系统托盘")
        # 使用新ToastManager (2026 UI组件)
        try:
            if hasattr(self, "_toast_manager") and self._toast_manager:
                self._toast_manager.info("程序正在后台运行，双击托盘图标可恢复窗口")
            else:
                ToastNotification(
                    self.root,
                    "程序已最小化",
                    "程序正在后台运行\n双击托盘图标可恢复窗口",
                    "info",
                    duration_ms=3000,
                )
        except Exception:
            return None

    def _restore_from_tray(self):
        """从托盘恢复窗口"""
        self._get_main_window_coordinator().restore_from_tray()

    def _update_summarizer_status_display(self):
        """更新摘要器状态显示 — 委托给 SettingsPage"""
        if hasattr(self, "settings_page"):
            self.settings_page.update_summarizer_status_display()

    def _refresh_summarizer_menus(self):
        """刷新摘要方法下拉菜单"""
        available_methods = [name for name, info in self._summarizer_info.items() if info.available]
        if not available_methods:
            available_methods = ["simple"]
        if hasattr(self, "method_menu"):
            self.method_menu.configure(values=available_methods)
            if self.method_var.get() not in available_methods:
                self.method_var.set(available_methods[0])
        if (
            hasattr(self, "batch_method_var")
            and self.batch_method_var.get() not in available_methods
        ):
            self.batch_method_var.set(available_methods[0])

    def _build_log_panel(self):
        """构建日志面板 - 委托给 LogPanel 组件"""
        self.log_panel = LogPanel(
            self.main_container,
            get_font=self._get_font,
            root=self.root,
            on_status_change=self._set_status,
        )
        self.log_panel.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))
        # 向后兼容的属性别名
        self.log_text = self.log_panel.log_text
        self.log_toggle_btn = self.log_panel.log_toggle_btn
        self._log_expanded = True

    def _show_page(self, page_id: str):
        """切换页面"""
        self._get_main_window_coordinator().show_page(page_id)

    def _show_page_animated(self, page_id: str):
        """带平滑滑动动画的页面切换"""
        return self._get_main_window_coordinator().show_page_animated(page_id)

    def _fade_in_page(self, page_id: str):
        """淡入新页面并更新导航按钮状态 (兼容旧代码)"""
        return self._get_main_window_coordinator().fade_in_page(page_id)

    def _update_nav_buttons_animated(self, active_page_id: str):
        """带平滑过渡动画更新导航按钮状态"""
        self._get_main_window_coordinator().update_nav_buttons_animated(active_page_id)

    def _animate_status_change(self, text: str):
        """动画状态变化"""
        self._set_status(text, ModernColors.INFO)
        self.root.after(1500, lambda: self._set_status("就绪", ModernColors.SUCCESS))

    def _on_theme_change(self, value: str):
        """主题切换 - 全链路联动"""
        mode = "light" if value == "浅色" else "dark"
        ctk.set_appearance_mode(mode)
        self._appearance_mode = mode

        # 同步更新 Windows 11 标题栏颜色
        Windows11StyleHelper.update_titlebar_color(self.root, mode)

        # 递归更新所有自定义组件的主题（ModernButton/Card/Input/Progress）
        self._broadcast_theme(mode)

        self._animate_status_change(f"已切换到{value}主题")

    def _broadcast_theme(self, mode: str) -> None:
        """递归广播主题到所有自定义组件"""
        for page in self._page_frames.values():
            self._update_widget_theme_recursive(page, mode)
        if hasattr(self, "sidebar") and self.sidebar:
            self._update_widget_theme_recursive(self.sidebar, mode)

    @staticmethod
    def _update_widget_theme_recursive(widget, mode: str) -> None:
        """深度优先遍历组件树，调用 update_theme"""
        if hasattr(widget, "update_theme") and callable(widget.update_theme):
            with contextlib.suppress(Exception):
                widget.update_theme(mode)
        for child in widget.winfo_children():
            WechatSummarizerGUI._update_widget_theme_recursive(child, mode)

    def _set_status(self, text: str, color: str = ModernColors.SUCCESS, pulse: bool = False):
        """设置状态 - 支持脉冲动画效果\n        \n        Args:\n            text: 状态文本\n            color: 状态颜色\n            pulse: 是否启用脉冲动画（用于进行中的状态）\n"""
        self.status_label.configure(text=f"● {text}", text_color=color)
        if hasattr(self, "_pulse_animation_id") and self._pulse_animation_id:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._pulse_animation_id)
            self._pulse_animation_id = None
        if pulse:
            self._start_pulse_animation(color)

    def _start_pulse_animation(self, base_color: str):
        """启动状态脉冲动画 - 交替明暗显示进行中"""
        self._pulse_phase = 0
        bright_color = adjust_color_brightness(base_color, 1.4)
        dim_color = adjust_color_brightness(base_color, 0.7)

        def pulse_step():
            if not hasattr(self, "_pulse_phase"):
                return None
            else:
                self._pulse_phase = (self._pulse_phase + 1) % 60
                import math

                t = (math.sin(self._pulse_phase * math.pi / 30) + 1) / 2
                try:
                    br = int(bright_color.lstrip("#")[0:2], 16)
                    bg = int(bright_color.lstrip("#")[2:4], 16)
                    bb = int(bright_color.lstrip("#")[4:6], 16)
                    dr = int(dim_color.lstrip("#")[0:2], 16)
                    dg = int(dim_color.lstrip("#")[2:4], 16)
                    db = int(dim_color.lstrip("#")[4:6], 16)
                    r = int(dr + (br - dr) * t)
                    g = int(dg + (bg - dg) * t)
                    b = int(db + (bb - db) * t)
                    current_color = f"#{r:02x}{g:02x}{b:02x}"
                    self.status_label.configure(text_color=current_color)
                except Exception:
                    pass
                self._pulse_animation_id = self.root.after(50, pulse_step)

        pulse_step()

    def _stop_pulse_animation(self):
        """停止脉冲动画"""
        if hasattr(self, "_pulse_animation_id") and self._pulse_animation_id:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._pulse_animation_id)
            self._pulse_animation_id = None

    def _refresh_availability(self):
        """刷新可用性"""
        self._summarizer_info = self._get_summarizer_info()
        self._exporter_info = self._get_exporter_info()
        if hasattr(self, "summarizer_status_frame"):
            self._update_summarizer_status_display()
        self._refresh_summarizer_menus()
        logger.info("已刷新服务状态")
        self._set_status("已刷新", ModernColors.SUCCESS)

    def _is_valid_wechat_url(self, url: str) -> bool:
        """检查是否为有效的微信公众号链接"""
        import re

        patterns = [
            "https?://mp\\.weixin\\.qq\\.com/s[/?]",
            "https?://mp\\.weixin\\.qq\\.com/s/[\\w\\-]+",
        ]
        return any(re.match(pattern, url.strip()) for pattern in patterns)

    def _on_url_input_change(self, event=None):
        """单篇处理URL输入变化时的验证"""
        url = self.url_entry.get().strip()
        if not url:
            self.url_status_label.configure(text="", text_color="gray")
            return None
        else:
            if self._is_valid_wechat_url(url):
                self.url_status_label.configure(
                    text="✓ 有效的微信公众号链接", text_color=ModernColors.SUCCESS
                )
            else:
                self.url_status_label.configure(
                    text="✗ 请输入有效的微信公众号文章链接", text_color=ModernColors.ERROR
                )

    def _on_batch_url_input_change(self, event=None):
        """批量处理URL输入变化时的验证和去重"""
        content = self.batch_url_text.get("1.0", "end").strip()
        if not content:
            self.batch_url_status_label.configure(text="", text_color="gray")
            return None
        else:
            lines = [line.strip() for line in content.split("\n") if line.strip()]
            if not lines:
                self.batch_url_status_label.configure(text="", text_color="gray")
                return None
            else:
                valid_urls = []
                invalid_urls = []
                for url in lines:
                    if self._is_valid_wechat_url(url):
                        valid_urls.append(url)
                    else:
                        if url.startswith("http"):
                            invalid_urls.append(url)
                unique_urls = []
                duplicate_count = 0
                seen = set()
                for url in valid_urls:
                    if url in seen:
                        duplicate_count += 1
                    else:
                        seen.add(url)
                        unique_urls.append(url)
                if duplicate_count > 0:
                    self.batch_url_text.index("insert")
                    self.batch_url_text.delete("1.0", "end")
                    self.batch_url_text.insert("1.0", "\n".join(unique_urls))
                    messagebox.showinfo(
                        "已自动去重", f"检测到 {duplicate_count} 个重复链接\n已自动删除重复项"
                    )
                    logger.info(f"已自动删除 {duplicate_count} 个重复链接")
                total_count = len(unique_urls)
                invalid_count = len(invalid_urls)
                if total_count > 0 and invalid_count == 0:
                    self.batch_url_status_label.configure(
                        text=f"✓ 共 {total_count} 个有效链接", text_color=ModernColors.SUCCESS
                    )
                    return None
                else:
                    if total_count > 0 and invalid_count > 0:
                        self.batch_url_status_label.configure(
                            text=f"✓ {total_count} 个有效 | ✗ {invalid_count} 个无效",
                            text_color=ModernColors.WARNING,
                        )
                    else:
                        self.batch_url_status_label.configure(
                            text="✗ 未找到有效的微信公众号链接", text_color=ModernColors.ERROR
                        )

    def _on_fetch(self):
        """处理抓取"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入文章URL")
            return None
        else:
            if not self._is_valid_wechat_url(url) and (
                not messagebox.askyesno(
                    "提示", "输入的链接可能不是有效的微信公众号链接\n\n是否继续处理？"
                )
            ):
                return None

            # 设置任务状态（用于退出确认）
            self._single_processing_active = True

            self.fetch_btn.configure(state="disabled")
            self._set_status("正在抓取...", ModernColors.INFO, pulse=True)
            logger.info(f"开始抓取: {url}")
            threading.Thread(target=self._fetch_article, args=(url,), daemon=True).start()

    def _fetch_article(self, url: str):
        """后台抓取"""
        try:
            article = self.container.fetch_use_case.execute(url)
            logger.info(f"抓取成功: {article.title}")
            if self.summarize_var.get():
                method = self.method_var.get()
                try:
                    logger.info(f"正在生成摘要 ({method})...")
                    summary = self.container.summarize_use_case.execute(article, method=method)
                    article.attach_summary(summary)
                    logger.success("摘要生成完成")
                except Exception as e:
                    logger.warning(f"摘要生成失败: {e}")
            self.current_article = article
            self.root.after(0, lambda: self._display_result(article))
        except Exception as e:
            logger.error(f"处理失败: {e}")
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._show_error(msg))

    def _display_result(self, article: Article):
        """显示结果"""
        # 清除任务状态
        self._single_processing_active = False

        self.title_label.configure(text=f"标题: {article.title}")
        self.author_label.configure(text=f"公众号: {article.account_name or '未知'}")
        self.word_count_label.configure(text=f"字数: {article.word_count}")
        self.preview_text.delete("1.0", "end")
        preview = (
            article.content_text[:2000] + "..."
            if len(article.content_text) > 2000
            else article.content_text
        )
        self.preview_text.insert("1.0", preview)
        self.summary_text.delete("1.0", "end")
        if article.summary:
            self.summary_text.insert("1.0", article.summary.content)
            self.points_text.delete("1.0", "end")
            if article.summary.key_points:
                points = "\n".join(f"• {p}" for p in article.summary.key_points)
                self.points_text.insert("1.0", points)
        self.export_btn.configure(state="normal")
        self.fetch_btn.configure(state="normal")
        self._set_status("处理完成", ModernColors.SUCCESS, pulse=False)

    def _show_error(self, message: str):
        """显示错误"""
        # 清除任务状态
        self._single_processing_active = False

        self.fetch_btn.configure(state="normal")
        self._set_status("处理失败", ModernColors.ERROR, pulse=False)
        messagebox.showerror("错误", message)

    def _check_export_dir_configured(self) -> bool:
        """检查导出目录是否已配置

        如果未配置导出目录，弹窗提醒用户设置。

        Returns:
            bool: True 如果已配置或用户选择继续，False 如果用户选择去设置
        """
        # 检查用户偏好中的导出目录
        user_export_dir = self.user_prefs.export_dir

        # 检查配置文件中的默认目录
        default_export_dir = (
            self.settings.export.default_output_dir if hasattr(self.settings, "export") else None
        )

        # 如果两者都未配置，则提醒用户
        if not user_export_dir and not default_export_dir:
            result = messagebox.askyesno(
                "导出目录未设置",
                "您尚未设置默认导出目录。\n\n"
                "建议在「设置」页面配置导出目录，这样每次导出时会自动定位到该目录。\n\n"
                "是否继续导出？\n"
                "\n· 点击「是」继续导出（每次需手动选择位置）"
                "\n· 点击「否」前往设置页配置导出目录",
                icon="warning",
            )

            if not result:
                # 用户选择去设置
                self._show_page_animated(self.PAGE_SETTINGS)
                # 显示提示
                if hasattr(self, "_toast_manager") and self._toast_manager:
                    self._toast_manager.info("请在下方「导出设置」中配置默认导出目录")
                return False

        return True

    def _on_export(self):
        """导出"""
        if not self.current_article:
            return None

        # 检查导出目录配置
        if not self._check_export_dir_configured():
            return None

        export_window = ctk.CTkToplevel(self.root)
        export_window.title("导出选项")
        export_window.geometry("400x350")
        export_window.transient(self.root)
        ctk.CTkLabel(
            export_window, text="📥 选择导出格式", font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)

        def export_as(target: str):
            export_window.destroy()
            if target == "word":
                self._show_word_preview()
            else:
                self._do_export(target)

        for name, info in self._exporter_info.items():
            btn_text = f"{('✓' if info.available else '✗')} {name.upper()}"
            if name == "word" and info.available:
                btn_text += " (预览)"
            btn = ctk.CTkButton(
                export_window,
                text=btn_text,
                font=ctk.CTkFont(size=14),
                height=45,
                corner_radius=10,
                fg_color=ModernColors.INFO if info.available else ModernColors.NEUTRAL_BTN_DISABLED,
                state="normal" if info.available else "disabled",
                command=lambda t=name: export_as(t),
            )
            btn.pack(fill="x", padx=30, pady=5)
            if not info.available and info.reason:
                ctk.CTkLabel(
                    export_window, text=info.reason, font=ctk.CTkFont(size=11), text_color="gray"
                ).pack()

    def _show_word_preview(self):
        """Word预览 - 委托给 dialogs.word_preview"""
        show_word_preview(self)

    def _show_batch_word_preview(self):
        """批量Word预览 - 委托给 dialogs.word_preview"""
        show_batch_word_preview(self)

    def _build_content_preview_with_images(self, article: Article) -> str:
        """构建带图片位置标记的内容预览 - 委托给 dialogs.word_preview"""
        return build_content_preview_with_images(article)

    def _extract_images_from_article(self, article: Article) -> list[str]:
        """提取图片 - 委托给 dialogs.word_preview"""
        return extract_images_from_article(article)

    def _do_export(self, target: str):
        """执行导出"""
        if not self.current_article:
            return None
        else:
            logger.info(f"开始导出: {target}")
            ext_map = {
                "html": (".html", "HTML文件", "*.html"),
                "markdown": (".md", "Markdown文件", "*.md"),
                "word": (".docx", "Word文档", "*.docx"),
                "zip": (".zip", "ZIP文件", "*.zip"),
            }
            ext_info = ext_map.get(target, (".html", "HTML文件", "*.html"))
            initial_dir = None
            if self.user_prefs.remember_export_dir and self.user_prefs.export_dir:
                dir_path = Path(self.user_prefs.export_dir)
                if dir_path.exists():
                    initial_dir = str(dir_path)
            if not initial_dir:
                default_dir = self.settings.export.default_output_dir
                if default_dir and Path(default_dir).exists():
                    initial_dir = default_dir
            path = filedialog.asksaveasfilename(
                defaultextension=ext_info[0],
                filetypes=[(ext_info[1], ext_info[2])],
                initialfile=f"{self.current_article.title[:30]}{ext_info[0]}",
                initialdir=initial_dir,
            )
            if not path:
                logger.info("导出已取消")
                return None
            else:
                if self.user_prefs.remember_export_dir:
                    export_dir = str(Path(path).parent)
                    if export_dir != self.user_prefs.export_dir:
                        self.user_prefs.export_dir = export_dir
                        logger.info(f"已记住导出目录: {export_dir}")
                self.export_btn.configure(state="disabled")
                self._set_status("正在导出...", ModernColors.INFO)

                def do_export():
                    try:
                        logger.info(f"导出路径: {path}")
                        result = self.container.export_use_case.execute(
                            self.current_article, target=target, path=path
                        )
                        logger.success(f"导出成功: {result}")
                        self.root.after(0, lambda: self._export_complete(True, str(result)))
                    except Exception as e:
                        logger.error(f"导出失败: {e}")
                        error_msg = str(e)
                        self.root.after(0, lambda msg=error_msg: self._export_complete(False, msg))

                threading.Thread(target=do_export, daemon=True).start()

    def _export_complete(self, success: bool, message: str):
        """导出完成"""
        self.export_btn.configure(state="normal")
        if success:
            self._set_status("导出完成", ModernColors.SUCCESS)
            messagebox.showinfo("成功", f"导出成功: {message}")
        else:
            self._set_status("导出失败", ModernColors.ERROR)
            messagebox.showerror("错误", f"导出失败: {message}")

    def _on_import_urls(self):
        """导入URL"""
        path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return None
        else:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                self.batch_url_text.delete("1.0", "end")
                self.batch_url_text.insert("1.0", content)
                logger.info(f"已导入URL文件: {path}")
            except Exception as e:
                messagebox.showerror("错误", f"读取失败: {e}")

    def _on_paste_urls(self):
        """粘贴URL"""
        try:
            content = self.root.clipboard_get()
            self.batch_url_text.insert("end", content)
        except Exception:
            messagebox.showwarning("提示", "剪贴板为空")

    def _on_batch_process(self):
        """批量处理"""
        content = self.batch_url_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("提示", "请输入URL")
            return None
        else:
            urls = [line.strip() for line in content.split("\n") if line.strip()]
            if not urls:
                messagebox.showwarning("提示", "未找到有效URL")
                return None
            else:
                self._start_batch_processing(urls)

    def _start_batch_processing(self, urls: list[str]):
        """开始批量处理"""
        self.batch_urls = urls
        self.batch_results = []
        self._batch_cancel_requested = False
        self._batch_progress_tracker = BatchProgressTracker(
            total=len(urls), smoothing_factor=0.3, log_interval=1
        )
        self._batch_progress_tracker.set_callback(self._on_batch_progress_update)
        # 切换开始/停止按钮状态
        if hasattr(self, "batch_page"):
            self.batch_page.set_processing_state(True)
        else:
            self.batch_start_btn.configure(state="disabled")
        self.batch_progress.set(0)
        self.batch_status_label.configure(text=f"正在处理 0/{len(urls)} 篇...")
        self.batch_elapsed_label.configure(text="00:00")
        self.batch_eta_label.configure(text="--:--")
        self.batch_rate_label.configure(text="计算中...")
        self.batch_count_label.configure(text="0 / 0")

        # 设置任务状态（用于退出确认）
        self._batch_processing_active = True

        logger.info(f"🚀 开始批量处理 {len(urls)} 篇文章")
        for widget in self.batch_result_frame.winfo_children():
            widget.destroy()
        threading.Thread(target=self._batch_process_worker, daemon=True).start()

    def _on_batch_progress_update(self, info: ProgressInfo):
        """进度更新回调（在工作线程中调用）"""
        self.root.after(0, lambda: self._update_batch_progress_ui(info))

    def _update_batch_progress_ui(self, info: ProgressInfo):
        """更新批量处理的GUI进度显示（在主线程中调用）"""
        progress_value = info.percentage / 100.0
        self.batch_progress.set(progress_value)
        self.batch_status_label.configure(
            text=f"正在处理 {info.progress_text} ({info.percentage_text})"
        )
        self.batch_elapsed_label.configure(text=info.elapsed_formatted)
        self.batch_eta_label.configure(text=info.eta_formatted)
        self.batch_rate_label.configure(text=info.rate_formatted)
        if hasattr(self, "_batch_progress_tracker"):
            tracker = self._batch_progress_tracker
            self.batch_count_label.configure(
                text=f"{tracker.success_count} / {tracker.failure_count}"
            )

    def _batch_process_worker(self):
        """批量处理工作线程"""
        method = self.batch_method_var.get()
        len(self.batch_urls)
        tracker = self._batch_progress_tracker
        for _i, url in enumerate(self.batch_urls):
            # 检查取消标志
            if getattr(self, "_batch_cancel_requested", False):
                logger.info("ℹ️ 用户取消了批量处理")
                break
            short_url = url[:50] + "..." if len(url) > 50 else url
            try:
                article = self.container.fetch_use_case.execute(url)
                try:
                    summary = self.container.summarize_use_case.execute(article, method=method)
                    article.attach_summary(summary)
                except Exception as e:
                    logger.warning(f"摘要失败: {e}")
                self.batch_results.append(article)
                tracker.update_success(current_item=article.title[:30])
                self.root.after(0, lambda a=article: self._add_batch_result_item(a, True))
            except Exception as e:
                logger.error(f"处理失败 {short_url}: {e}")
                tracker.update_failure(current_item=short_url, error=str(e))
                self.root.after(
                    0, lambda u=url, err=str(e): self._add_batch_result_item_error(u, err)
                )
        tracker.finish()
        self.root.after(0, self._batch_process_complete)

    def _update_batch_progress(self, value: float, status: str):
        """更新批量进度（兼容旧接口）"""
        self.batch_progress.set(value)
        self.batch_status_label.configure(text=status)

    def _add_batch_result_item(self, article: Article, success: bool):
        """添加批量结果项"""
        frame = ctk.CTkFrame(
            self.batch_result_frame,
            corner_radius=8,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
        )
        frame.pack(fill="x", pady=3)
        icon = "✓" if success else "✗"
        color = ModernColors.SUCCESS if success else ModernColors.ERROR
        title = article.title[:35] + "..." if len(article.title) > 35 else article.title
        ctk.CTkLabel(frame, text=f"{icon} {title}", anchor="w", text_color=color).pack(
            side="left", padx=10, pady=8, fill="x", expand=True
        )

    def _add_batch_result_item_error(self, url: str, error: str):
        """添加错误项"""
        frame = ctk.CTkFrame(
            self.batch_result_frame,
            corner_radius=8,
            fg_color=(ModernColors.LIGHT_INSET, ModernColors.DARK_INSET),
        )
        frame.pack(fill="x", pady=3)
        short_url = url[:25] + "..." if len(url) > 25 else url
        ctk.CTkLabel(frame, text=f"✗ {short_url}", anchor="w", text_color=ModernColors.ERROR).pack(
            side="left", padx=10, pady=8
        )
        ctk.CTkLabel(frame, text=error[:30], text_color="gray", font=ctk.CTkFont(size=11)).pack(
            side="right", padx=10, pady=8
        )

    def _batch_process_complete(self):
        """批量处理完成"""
        # 清除任务状态
        self._batch_processing_active = False
        self._batch_cancel_requested = False

        # 恢复按钮状态
        if hasattr(self, "batch_page"):
            self.batch_page.set_processing_state(False)
        else:
            self.batch_start_btn.configure(state="normal")
        self.batch_progress.set(1.0)
        success_count = len(self.batch_results)
        total = len(self.batch_urls)
        self.batch_status_label.configure(text=f"完成: {success_count}/{total} 篇成功")
        logger.success(f"批量处理完成: {success_count}/{total}")
        if self.batch_results:
            self.batch_export_btn.configure(state="normal")
            self.batch_export_md_btn.configure(state="normal")
            self.batch_export_word_btn.configure(state="normal")
            self.batch_export_html_btn.configure(state="normal")

    def _on_batch_export(self):
        """批量压缩导出 - 支持多格式和文章选择"""
        if not self.batch_results:
            return None

        # 检查导出目录配置
        if not self._check_export_dir_configured():
            return None

        # 显示批量压缩导出对话框
        dialog = BatchArchiveExportDialog(self.root, self.batch_results)
        result = dialog.get()

        if not result:
            return None  # 用户取消

        # 执行多格式压缩导出
        self._do_archive_export(
            articles=result["articles"], archive_format=result["format"], path=result["path"]
        )

    def _do_archive_export(self, articles: list, archive_format: str, path: str):
        """执行多格式压缩导出（带进度跟踪）

        Args:
            articles: 要导出的文章列表
            archive_format: 压缩格式 ('zip', '7z', 'rar')
            path: 输出路径
        """
        self._disable_export_buttons()
        self._archive_export_articles = articles  # 保存要导出的文章
        self._archive_progress_tracker = BatchProgressTracker(
            total=len(articles), smoothing_factor=0.3, log_interval=1
        )
        self._archive_progress_tracker.set_callback(self._on_export_progress_update)
        self.batch_progress.set(0)

        format_names = {"zip": "ZIP", "7z": "7z", "rar": "RAR"}
        format_name = format_names.get(archive_format, archive_format.upper())

        self.batch_status_label.configure(text=f"正在打包 0/{len(articles)} 篇为 {format_name}...")
        self.batch_elapsed_label.configure(text="00:00")
        self.batch_eta_label.configure(text="--:--")
        self.batch_rate_label.configure(text="计算中...")
        self.batch_count_label.configure(text="0 / 0")

        # 设置任务状态（用于退出确认）
        self._batch_export_active = True

        logger.info(f"📦 开始导出 {len(articles)} 篇文章为 {format_name} 压缩包")
        threading.Thread(
            target=self._archive_export_worker, args=(articles, archive_format, path), daemon=True
        ).start()

    def _archive_export_worker(self, articles: list, archive_format: str, path: str):
        """工作线程：执行多格式压缩导出"""
        try:
            from ...infrastructure.adapters.exporters import MultiFormatArchiveExporter

            tracker = self._archive_progress_tracker

            def progress_callback(current: int, total: int, item_name: str):
                if current > tracker.current:
                    tracker.update_success(current_item=item_name)

            # 创建多格式压缩导出器
            exporter = MultiFormatArchiveExporter()
            result = exporter.export_batch(
                articles=articles,
                path=path,
                archive_format=archive_format,
                progress_callback=progress_callback,
            )

            tracker.finish()
            self.root.after(0, lambda: self._archive_export_complete(result, archive_format))
        except Exception as e:
            logger.error(f"压缩导出失败: {e}")
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._archive_export_error(msg))

    def _archive_export_complete(self, result: str, archive_format: str):
        """处理压缩导出完成"""
        # 清除任务状态
        self._batch_export_active = False

        self._enable_export_buttons()
        self.batch_progress.set(1.0)

        format_names = {"zip": "ZIP", "7z": "7z", "rar": "RAR"}
        format_name = format_names.get(archive_format, archive_format.upper())

        self.batch_status_label.configure(text=f"{format_name} 导出完成")
        logger.success(f"批量导出成功: {result}")
        messagebox.showinfo("成功", f"导出成功: {result}")

    def _archive_export_error(self, error: str):
        """处理压缩导出错误"""
        # 清除任务状态
        self._batch_export_active = False

        self._enable_export_buttons()
        self.batch_status_label.configure(text="压缩导出失败")
        messagebox.showerror("错误", f"导出失败: {error}")

    def _on_batch_export_format(self, target: str):
        """批量导出指定格式"""
        if not self.batch_results:
            return None

        # 检查导出目录配置
        if not self._check_export_dir_configured():
            return None

        if target == "word":
            self._show_batch_word_preview()
            return None
        else:
            dir_path = filedialog.askdirectory(title="选择输出目录")
            if not dir_path:
                return None
            else:
                self._do_batch_export(target, dir_path)

    def _do_batch_export(self, target: str, dir_path: str):
        """执行批量导出（在后台线程中执行）"""
        self._disable_export_buttons()
        self._export_progress_tracker = BatchProgressTracker(
            total=len(self.batch_results), smoothing_factor=0.3, log_interval=1
        )
        self._export_progress_tracker.set_callback(self._on_export_progress_update)
        self.batch_progress.set(0)
        self.batch_status_label.configure(text=f"正在导出 0/{len(self.batch_results)} 篇...")
        self.batch_elapsed_label.configure(text="00:00")
        self.batch_eta_label.configure(text="--:--")
        self.batch_rate_label.configure(text="计算中...")
        self.batch_count_label.configure(text="0 / 0")

        # 设置任务状态（用于退出确认）
        self._batch_export_active = True

        logger.info(f"📤 开始批量导出 {len(self.batch_results)} 篇文章为 {target.upper()} 格式")
        threading.Thread(
            target=self._batch_export_worker, args=(target, dir_path), daemon=True
        ).start()

    def _on_export_progress_update(self, info: ProgressInfo):
        """导出进度更新回调"""
        self.root.after(0, lambda: self._update_export_progress_ui(info))

    def _update_export_progress_ui(self, info: ProgressInfo):
        """更新导出进度GUI显示"""
        progress_value = info.percentage / 100.0
        self.batch_progress.set(progress_value)
        self.batch_status_label.configure(
            text=f"正在导出 {info.progress_text} ({info.percentage_text})"
        )
        self.batch_elapsed_label.configure(text=info.elapsed_formatted)
        self.batch_eta_label.configure(text=info.eta_formatted)
        self.batch_rate_label.configure(text=info.rate_formatted)
        if hasattr(self, "_export_progress_tracker"):
            tracker = self._export_progress_tracker
            self.batch_count_label.configure(
                text=f"{tracker.success_count} / {tracker.failure_count}"
            )

    def _batch_export_worker(self, target: str, dir_path: str):
        """批量导出工作线程"""
        try:
            output_dir = Path(dir_path)
            tracker = self._export_progress_tracker
            ext_map = {"markdown": ".md", "html": ".html", "word": ".docx"}
            ext = ext_map.get(target, ".html")
            for article in self.batch_results:
                try:
                    safe_title = "".join(
                        c for c in article.title[:50] if c.isalnum() or c in " _-"
                    ).strip()
                    file_path = output_dir / f"{safe_title}{ext}"
                    self.container.export_use_case.execute(
                        article, target=target, path=str(file_path)
                    )
                    tracker.update_success(current_item=article.title[:30])
                except Exception as e:
                    logger.warning(f"导出失败 {article.title}: {e}")
                    tracker.update_failure(current_item=article.title[:30], error=str(e))
            tracker.finish()
            self.root.after(
                0,
                lambda: self._batch_export_complete(
                    tracker.success_count, tracker.failure_count, dir_path
                ),
            )
        except Exception as e:
            logger.error(f"导出失败: {e}")
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self._batch_export_error(msg))

    def _batch_export_complete(self, success_count: int, failure_count: int, dir_path: str):
        """批量导出完成"""
        # 清除任务状态
        self._batch_export_active = False

        self._enable_export_buttons()
        self.batch_progress.set(1.0)
        self.batch_status_label.configure(
            text=f"导出完成: {success_count} 成功, {failure_count} 失败"
        )
        total = success_count + failure_count
        logger.success(f"批量导出完成: {success_count}/{total}")
        messagebox.showinfo("成功", f"导出完成: {success_count}/{total} 篇\n输出目录: {dir_path}")

    def _batch_export_error(self, error: str):
        """批量导出出错"""
        # 清除任务状态
        self._batch_export_active = False

        self._enable_export_buttons()
        self.batch_status_label.configure(text="导出失败")
        messagebox.showerror("错误", f"导出失败: {error}")

    def _disable_export_buttons(self):
        """禁用所有导出按钮"""
        self.batch_export_btn.configure(state="disabled")
        self.batch_export_md_btn.configure(state="disabled")
        self.batch_export_word_btn.configure(state="disabled")
        self.batch_export_html_btn.configure(state="disabled")

    def _enable_export_buttons(self):
        """启用所有导出按钮"""
        if self.batch_results:
            self.batch_export_btn.configure(state="normal")
            self.batch_export_md_btn.configure(state="normal")
            self.batch_export_word_btn.configure(state="normal")
            self.batch_export_html_btn.configure(state="normal")

    def _refresh_history(self):
        """刷新历史 — 委托给 HistoryPage"""
        if hasattr(self, "history_page"):
            self.history_page._refresh_history()

    def run(self):
        """运行GUI"""
        self.root.mainloop()


def run_gui(
    runtime: AppRuntime | None = None,
    *,
    container: Container | None = None,
    settings: AppSettings | None = None,
):
    """启动GUI（组合根 - 创建依赖并注入）"""
    if not _ctk_available:
        print("错误: customtkinter未安装")
        print("请运行: pip install customtkinter")
        return None

    if runtime is not None:
        if container is not None and runtime.container is not container:
            raise ValueError("runtime.container 与 container 必须保持一致")
        if settings is not None and runtime.settings is not settings:
            raise ValueError("runtime.settings 与 settings 必须保持一致")
        resolved_runtime = runtime
    else:
        resolved_runtime = build_app_runtime(settings=settings, container=container)

    app = WechatSummarizerGUI(
        container=resolved_runtime.container,
        settings=resolved_runtime.settings,
    )
    app.run()


if __name__ == "__main__":
    run_gui()
