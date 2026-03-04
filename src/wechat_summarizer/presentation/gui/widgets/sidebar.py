"""Sidebar 侧边栏组件

从 WechatSummarizerGUI 提取的侧边导航栏和底部状态栏。
采用 CustomTkinter CTkFrame 子类化模式，接收回调函数实现解耦。
"""

from __future__ import annotations

from collections.abc import Callable

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from .tooltip import create_tooltip

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class Sidebar(ctk.CTkFrame):
    """侧边导航栏组件

    包含：
    - Logo 和标题
    - 导航按钮列表
    - 外观主题切换
    - 底部状态栏（摘要器/导出器/缓存状态）
    - 就绪状态指示器

    Args:
        master: 父容器
        get_font: 字体工厂函数 (size, weight='normal') -> CTkFont
        nav_items: 导航项列表 [(page_id, icon, text), ...]
        on_navigate: 页面切换回调 (page_id) -> None
        on_theme_change: 主题切换回调 (value) -> None
        summarizer_info: 摘要器信息字典
        exporter_info: 导出器信息字典
        container: 依赖注入容器（用于获取缓存状态）
    """

    def __init__(
        self,
        master,
        *,
        get_font: Callable,
        nav_items: list[tuple[str, str, str]],
        on_navigate: Callable[[str], None],
        on_theme_change: Callable[[str], None],
        summarizer_info: dict,
        exporter_info: dict,
        container,
        **kwargs,
    ):
        super().__init__(
            master,
            width=220,
            corner_radius=0,
            fg_color=(ModernColors.LIGHT_SIDEBAR, ModernColors.DARK_SIDEBAR),
            **kwargs,
        )

        self._get_font = get_font
        self._on_navigate = on_navigate
        self._on_theme_change = on_theme_change
        self._summarizer_info = summarizer_info
        self._exporter_info = exporter_info
        self._container = container

        # 公开属性，供外部访问
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.status_label: ctk.CTkLabel | None = None
        self.theme_switch: ctk.CTkSegmentedButton | None = None

        self._build(nav_items)

    def _build(self, nav_items: list[tuple[str, str, str]]):
        """构建侧边栏内容"""
        self.grid_rowconfigure(10, weight=1)

        # Logo 区域
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(25, 30), sticky="ew")

        title_label = ctk.CTkLabel(
            logo_frame,
            text="📰 文章助手",
            font=self._get_font(22, "bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            logo_frame,
            text="WeChat Article Summarizer",
            font=self._get_font(11),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
        )
        subtitle_label.pack(anchor="w")

        # 导航按钮
        for i, (page_id, icon, text) in enumerate(nav_items):
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {text}",
                font=self._get_font(14),
                height=45,
                anchor="w",
                corner_radius=Spacing.RADIUS_MD,
                fg_color="transparent",
                text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
                hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
                command=lambda p=page_id: self._on_navigate(p),
            )
            btn.grid(row=i + 1, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[page_id] = btn

        # 底部设置区域
        settings_frame = ctk.CTkFrame(self, fg_color="transparent")
        settings_frame.grid(row=11, column=0, padx=15, pady=15, sticky="sew")

        theme_label = ctk.CTkLabel(
            settings_frame,
            text="🎨 外观主题",
            font=self._get_font(12),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
        )
        theme_label.pack(anchor="w", pady=(0, 5))

        self.theme_switch = ctk.CTkSegmentedButton(
            settings_frame,
            values=["浅色", "深色"],
            command=self._on_theme_change,
            font=self._get_font(12),
        )
        self.theme_switch.set("深色")
        self.theme_switch.pack(fill="x")

        # 紧凑状态栏 - 类似 VS Code 底部状态栏设计
        self._build_status_bar(settings_frame)

        # 就绪状态指示器
        self.status_label = ctk.CTkLabel(
            settings_frame,
            text="● 就绪",
            font=self._get_font(11),
            text_color=ModernColors.SUCCESS,
        )
        self.status_label.pack(anchor="w", pady=(10, 0))

    def _build_status_bar(self, parent):
        """构建侧边栏底部状态栏 - 紧凑型状态指示器

        参考 VS Code 状态栏设计：
        - 状态栏位于底部，显示与工作区相关的信息
        - 使用紧凑的图标+文本形式
        - 点击可跳转到设置页查看详情
        """
        status_bar = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        status_bar.pack(fill="x", pady=(12, 0))

        # 计算状态
        summarizer_count = sum(1 for info in self._summarizer_info.values() if info.available)
        summarizer_total = len(self._summarizer_info)
        exporter_count = sum(1 for info in self._exporter_info.values() if info.available)
        exporter_total = len(self._exporter_info)

        # 状态指示器容器
        indicators = ctk.CTkFrame(status_bar, fg_color="transparent")
        indicators.pack(fill="x")

        # 摘要器状态 - 紧凑形式
        summarizer_ok = summarizer_count > 0
        summarizer_color = ModernColors.SUCCESS if summarizer_ok else ModernColors.ERROR
        summarizer_btn = ctk.CTkButton(
            indicators,
            text=f"● {summarizer_count}/{summarizer_total}",
            font=self._get_font(10),
            height=22,
            width=55,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            text_color=summarizer_color,
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=lambda: self._on_navigate("settings"),
        )
        summarizer_btn.pack(side="left", padx=(0, 4))
        create_tooltip(
            summarizer_btn,
            f"摘要器: {summarizer_count}/{summarizer_total} 可用\n点击查看详情",
            self._get_font,
        )

        # 导出器状态
        exporter_ok = exporter_count > 0
        exporter_color = ModernColors.SUCCESS if exporter_ok else ModernColors.ERROR
        exporter_btn = ctk.CTkButton(
            indicators,
            text=f"● {exporter_count}/{exporter_total}",
            font=self._get_font(10),
            height=22,
            width=55,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            text_color=exporter_color,
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=lambda: self._on_navigate("settings"),
        )
        exporter_btn.pack(side="left", padx=(0, 4))
        create_tooltip(
            exporter_btn,
            f"导出器: {exporter_count}/{exporter_total} 可用\n点击查看详情",
            self._get_font,
        )

        # 缓存状态
        try:
            storage = self._container.storage
            if storage:
                stats = storage.get_stats()
                cache_count = stats.total_entries
            else:
                cache_count = 0
        except Exception:
            cache_count = 0

        cache_btn = ctk.CTkButton(
            indicators,
            text=f"🗃 {cache_count}",
            font=self._get_font(10),
            height=22,
            width=50,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=lambda: self._on_navigate("history"),
        )
        cache_btn.pack(side="left")
        create_tooltip(
            cache_btn,
            f"缓存: {cache_count} 条记录\n点击查看历史记录",
            self._get_font,
        )
