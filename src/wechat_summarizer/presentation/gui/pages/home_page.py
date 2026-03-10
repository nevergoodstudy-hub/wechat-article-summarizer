"""首页 - 仪表盘

升级后的仪表盘首页，包含：
- 欢迎区域 + 快速粘贴入口
- Bento 网格快捷导航卡片
- 系统状态总览（摘要器/导出器/缓存）
- 最近处理记录
- 动态提示条
"""

from __future__ import annotations

import contextlib
import random
from typing import TYPE_CHECKING, Any

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import get_i18n
from ..widgets.helpers import adjust_color_brightness

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False

if TYPE_CHECKING:
    pass

# 简化提示列表 - 随机展示一条
_TIPS = [
    ("📋", "粘贴即用", "复制微信文章链接，直接粘贴到下方输入框即可开始处理"),
    ("⌨️", "快捷键", "Ctrl+1~4 切换页面，Ctrl+D 切换主题，Ctrl+E 导出"),
    ("🤖", "AI 摘要", "在设置中配置 API 密钥，即可使用 DeepSeek/OpenAI 智能摘要"),
    ("📦", "批量打包", "批量处理后可一键导出为 ZIP 压缩包"),
    ("🗃️", "智能缓存", "已处理文章自动缓存，重复链接秒速加载"),
    ("📂", "文件导入", "在批量页面点击「从文件导入」支持 .txt 批量导入链接"),
]


class HomePage(ctk.CTkFrame):
    """首页仪表盘

    Bento 网格布局：快捷导航 + 状态总览 + 最近记录 + 动态提示。

    Args:
        master: 父容器
        gui: WechatSummarizerGUI 控制器引用
    """

    PAGE_SINGLE = "single"
    PAGE_BATCH = "batch"
    PAGE_HISTORY = "history"
    PAGE_SETTINGS = "settings"

    def __init__(self, master, gui, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self._recent_labels: list[Any] = []
        self._build()

    def _navigate(self, page_id: str, *, animated: bool = False) -> None:
        """通过事件总线请求页面切换。"""
        self.gui.event_bus.publish("navigate", page_id=page_id, animated=animated)

    # ==================================================================
    # 构建
    # ==================================================================

    def _build(self):
        """构建仪表盘"""
        # 可滚动容器
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._scroll.grid_columnconfigure(0, weight=1)

        # ① 欢迎区 + 快速粘贴
        self._build_welcome(self._scroll)

        # ② 导航卡片 (Bento 3列)
        self._build_action_cards(self._scroll)

        # ③ 状态 + 最近记录 (2列)
        info_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        info_row.pack(fill="x", pady=(0, 10))
        info_row.grid_columnconfigure(0, weight=1)
        info_row.grid_columnconfigure(1, weight=2)

        self._build_status_overview(info_row)
        self._build_recent_records(info_row)

        # ④ 动态提示条
        self._build_tip_bar(self._scroll)

    # ------------------------------------------------------------------
    # ① 欢迎区 + 快速粘贴入口
    # ------------------------------------------------------------------

    def _build_welcome(self, parent):
        """欢迎区 + 快速粘贴URL入口"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            frame,
            text="👋 欢迎使用文章助手",
            font=self.gui._get_font(28, "bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        ).pack(anchor="w")

        ctk.CTkLabel(
            frame,
            text="快速抓取、总结和导出微信公众号文章",
            font=self.gui._get_font(14),
            text_color=(
                ModernColors.LIGHT_TEXT_SECONDARY,
                ModernColors.DARK_TEXT_SECONDARY,
            ),
        ).pack(anchor="w", pady=(5, 12))

        # 快速粘贴栏
        paste_row = ctk.CTkFrame(
            frame,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            corner_radius=Spacing.RADIUS_LG,
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        paste_row.pack(fill="x")

        inner = ctk.CTkFrame(paste_row, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self._quick_entry = ctk.CTkEntry(
            inner,
            placeholder_text="粘贴微信文章链接，按 Enter 开始处理…",
            font=self.gui._get_font(13),
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        self._quick_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self._quick_entry.bind("<Return>", self._on_quick_paste)

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

    def _on_quick_paste(self, _event):
        """快速粘贴处理"""
        url = self._quick_entry.get().strip()
        if not url:
            return
        # 跳转到单篇页面并填入URL
        self._navigate(self.PAGE_SINGLE)
        with contextlib.suppress(Exception):
            self.gui.url_entry.delete(0, "end")
            self.gui.url_entry.insert(0, url)
            self._quick_entry.delete(0, "end")

    # ------------------------------------------------------------------
    # ② 导航卡片
    # ------------------------------------------------------------------

    def _build_action_cards(self, parent):
        """Bento 网格导航卡片"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 15))
        cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        cards = [
            ("📄", "单篇处理", "抓取并生成摘要", self.PAGE_SINGLE, ModernColors.INFO),
            ("📚", "批量处理", "多篇文章批量处理", self.PAGE_BATCH, ModernColors.SUCCESS),
            ("📜", "历史记录", "查看已处理文章", self.PAGE_HISTORY, ModernColors.WARNING),
        ]
        for i, (icon, title, desc, page, color) in enumerate(cards):
            card = self._create_animated_card(
                cards_frame,
                icon=icon,
                title=title,
                desc=desc,
                color=color,
                command=lambda p=page: self._navigate(p),
            )
            card.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")

    # ------------------------------------------------------------------
    # ③-a 状态总览
    # ------------------------------------------------------------------

    def _build_status_overview(self, parent):
        """系统状态总览卡片"""
        card = ctk.CTkFrame(
            parent,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        card.grid(row=0, column=0, padx=(8, 6), pady=8, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(
            inner,
            text="📊 系统状态",
            font=self.gui._get_font(14, "bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        ).pack(anchor="w", pady=(0, 10))

        # 摘要器
        info = getattr(self.gui, "_summarizer_info", {})
        avail = sum(1 for v in info.values() if v.available)
        total = len(info)
        s_color = ModernColors.SUCCESS if avail > 0 else ModernColors.ERROR
        self._stat_row(inner, "🤖 摘要器", f"{avail}/{total} 可用", s_color)

        # 导出器
        exp = getattr(self.gui, "_exporter_info", {})
        e_avail = sum(1 for v in exp.values() if v.available)
        e_total = len(exp)
        e_color = ModernColors.SUCCESS if e_avail > 0 else ModernColors.ERROR
        self._stat_row(inner, "📤 导出器", f"{e_avail}/{e_total} 可用", e_color)

        # 缓存
        cache_count = 0
        with contextlib.suppress(Exception):
            storage = self.gui.container.storage
            if storage:
                cache_count = storage.get_stats().total_entries
        self._stat_row(inner, "🗃️ 缓存", f"{cache_count} 条记录", ModernColors.INFO)

        # 设置入口
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
            command=lambda: self._navigate(self.PAGE_SETTINGS),
        )
        settings_btn.pack(anchor="w", pady=(10, 0))

    def _stat_row(self, parent, label: str, value: str, color: str):
        """状态行"""
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

    # ------------------------------------------------------------------
    # ③-b 最近记录
    # ------------------------------------------------------------------

    def _build_recent_records(self, parent):
        """最近处理的文章列表"""
        card = ctk.CTkFrame(
            parent,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        card.grid(row=0, column=1, padx=(6, 8), pady=8, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
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
            command=lambda: self._navigate(self.PAGE_HISTORY),
        ).pack(side="right")

        self._recent_container = inner
        self._populate_recent_records()

    def _populate_recent_records(self):
        """填充最近记录列表"""
        # 清除旧标签
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

    def refresh_recent(self):
        """外部调用刷新最近记录（如处理完成后）"""
        self._populate_recent_records()

    # ------------------------------------------------------------------
    # ④ 动态提示条
    # ------------------------------------------------------------------

    def _build_tip_bar(self, parent):
        """底部随机提示条"""
        tip = random.choice(_TIPS)
        tip_frame = ctk.CTkFrame(
            parent,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
        )
        tip_frame.pack(fill="x", padx=8, pady=(5, 10))

        inner = ctk.CTkFrame(tip_frame, fg_color="transparent")
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

    # ------------------------------------------------------------------
    # 动画卡片
    # ------------------------------------------------------------------

    def _create_animated_card(
        self, parent, icon: str, title: str, desc: str, color: str, command=None
    ) -> ctk.CTkFrame:
        """带悬停动画的导航卡片"""
        card = ctk.CTkFrame(
            parent,
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

        def on_enter(e):
            card.configure(
                fg_color=(ModernColors.LIGHT_CARD_HOVER, ModernColors.DARK_CARD_HOVER),
                border_color=(color, color),
            )
            title_label.configure(text_color=adjust_color_brightness(color, 1.2))

        def on_leave(e):
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

    # ------------------------------------------------------------------
    # 提示轮播 (Legacy - 已弃用，保留备用)
    # ------------------------------------------------------------------

    def _build_tips_carousel_legacy(self, parent):
        """构建动态提示轮播组件 (已弃用 - 保留备用)

        采用 UX 最佳实践:
        - 自动轮播 + 手动切换
        - 简洁文案 (<180字符)
        - 分类标签 (快速开始/快捷键/进阶技巧)
        - 上下文相关提示
        """
        # 提示数据 - 分类组织
        self._tips_data = [
            # 快速开始类
            {
                "category": "🚀 快速开始",
                "category_en": "🚀 Quick Start",
                "icon": "📋",
                "title": "粘贴即用",
                "title_en": "Paste to Start",
                "content": "复制微信文章链接后，直接粘贴到「单篇处理」输入框即可开始",
                "content_en": "Copy a WeChat article URL and paste it into Single Article input",
                "color": ModernColors.INFO,
            },
            {
                "category": "🚀 快速开始",
                "category_en": "🚀 Quick Start",
                "icon": "📚",
                "title": "批量处理",
                "title_en": "Batch Processing",
                "content": "每行一个链接，支持同时处理数十篇文章，自动跳过无效链接",
                "content_en": "One URL per line, process dozens of articles at once",
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "🚀 快速开始",
                "category_en": "🚀 Quick Start",
                "icon": "🤖",
                "title": "AI 摘要",
                "title_en": "AI Summary",
                "content": "配置 API 密钥后可使用 DeepSeek/OpenAI 生成高质量智能摘要",
                "content_en": "Configure API keys to use DeepSeek/OpenAI for smart summaries",
                "color": ModernColors.GRADIENT_MID,
            },
            {
                "category": "🚀 快速开始",
                "category_en": "🚀 Quick Start",
                "icon": "📂",
                "title": "从文件导入",
                "title_en": "Import from File",
                "content": "在批量处理页面点击「从文件导入」，支持 .txt 文件批量导入链接",
                "content_en": 'Click "Import from File" in Batch page to load URLs from .txt file',
                "color": ModernColors.INFO,
            },
            # 快捷键类
            {
                "category": "⌨️ 快捷键",
                "category_en": "⌨️ Shortcuts",
                "icon": "⌨️",
                "title": "快速切换",
                "title_en": "Quick Switch",
                "content": "Ctrl+1/2/3/4 快速切换页面，Ctrl+D 切换深色/浅色主题",
                "content_en": "Ctrl+1/2/3/4 to switch pages, Ctrl+D to toggle dark/light theme",
                "color": ModernColors.WARNING,
            },
            {
                "category": "⌨️ 快捷键",
                "category_en": "⌨️ Shortcuts",
                "icon": "📥",
                "title": "快速导出",
                "title_en": "Quick Export",
                "content": "Ctrl+E 导出当前文章，Ctrl+Shift+E 批量打包导出",
                "content_en": "Ctrl+E to export, Ctrl+Shift+E for batch archive export",
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "⌨️ 快捷键",
                "category_en": "⌨️ Shortcuts",
                "icon": "📝",
                "title": "复制摘要",
                "title_en": "Copy Summary",
                "content": "点击摘要框右上角的复制按钮，一键复制摘要内容到剪贴板",
                "content_en": "Click copy button on summary box to copy content to clipboard",
                "color": ModernColors.INFO,
            },
            # 进阶技巧类
            {
                "category": "💡 进阶技巧",
                "category_en": "💡 Pro Tips",
                "icon": "📦",
                "title": "多格式打包",
                "title_en": "Multi-format Archive",
                "content": "支持 ZIP/7z/RAR 压缩格式，可选择部分文章打包导出",
                "content_en": "Export as ZIP/7z/RAR, select specific articles to include",
                "color": ModernColors.INFO,
            },
            {
                "category": "💡 进阶技巧",
                "category_en": "💡 Pro Tips",
                "icon": "🗃️",
                "title": "智能缓存",
                "title_en": "Smart Cache",
                "content": "已处理文章自动缓存，重复链接秒速加载，节省流量和时间",
                "content_en": "Processed articles are cached, duplicates load instantly",
                "color": ModernColors.WARNING,
            },
            {
                "category": "💡 进阶技巧",
                "category_en": "💡 Pro Tips",
                "icon": "🌐",
                "title": "多语言支持",
                "title_en": "Multi-language",
                "content": "在「设置」中切换界面语言，支持简体中文和英语",
                "content_en": "Switch UI language in Settings, supports Chinese and English",
                "color": ModernColors.GRADIENT_END,
            },
            {
                "category": "💡 进阶技巧",
                "category_en": "💡 Pro Tips",
                "icon": "📊",
                "title": "日志查看",
                "title_en": "View Logs",
                "content": "屏幕底部可展开日志面板，查看详细处理进度和错误信息",
                "content_en": "Expand log panel at bottom to view detailed progress and errors",
                "color": ModernColors.NEON_CYAN,
            },
            # 导出功能类
            {
                "category": "📄 导出功能",
                "category_en": "📄 Export Features",
                "icon": "📝",
                "title": "Word 导出",
                "title_en": "Word Export",
                "content": "导出为 .docx 格式，保留文章标题、正文、图片和摘要内容",
                "content_en": "Export as .docx with title, content, images and summary preserved",
                "color": ModernColors.INFO,
            },
            {
                "category": "📄 导出功能",
                "category_en": "📄 Export Features",
                "icon": "📜",
                "title": "Markdown 导出",
                "title_en": "Markdown Export",
                "content": "导出为 .md 格式，适合笔记软件或 Git 仓库存档",
                "content_en": "Export as .md format, ideal for note apps or Git repositories",
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "📄 导出功能",
                "category_en": "📄 Export Features",
                "icon": "🌐",
                "title": "HTML 导出",
                "title_en": "HTML Export",
                "content": "导出为完整网页格式，保留原文样式和图片，可离线查看",
                "content_en": "Export as full webpage, preserves styling and images for offline viewing",
                "color": ModernColors.WARNING,
            },
            # 效率技巧类
            {
                "category": "⚡ 效率技巧",
                "category_en": "⚡ Efficiency Tips",
                "icon": "⏱️",
                "title": "实时进度",
                "title_en": "Real-time Progress",
                "content": "批量处理时可查看实时进度、已用时间、预估剩余和处理速率",
                "content_en": "View real-time progress, elapsed time, ETA and processing speed",
                "color": ModernColors.INFO,
            },
            {
                "category": "⚡ 效率技巧",
                "category_en": "⚡ Efficiency Tips",
                "icon": "🚨",
                "title": "任务中断",
                "title_en": "Stop Processing",
                "content": "批量处理过程中可随时点击「停止」按钮，已处理的文章会保留",
                "content_en": 'Click "Stop" anytime during batch processing, completed articles are kept',
                "color": ModernColors.ERROR,
            },
            {
                "category": "⚡ 效率技巧",
                "category_en": "⚡ Efficiency Tips",
                "icon": "🔄",
                "title": "刷新缓存",
                "title_en": "Refresh Cache",
                "content": "在历史记录页点击「刷新」按钮可重新加载缓存列表",
                "content_en": 'Click "Refresh" in History page to reload cache list',
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "⚡ 效率技巧",
                "category_en": "⚡ Efficiency Tips",
                "icon": "🧹",
                "title": "清理缓存",
                "title_en": "Clear Cache",
                "content": "在历史记录页点击「清空缓存」释放磁盘空间，需谨慎操作",
                "content_en": 'Click "Clear Cache" in History to free disk space, use with caution',
                "color": ModernColors.WARNING,
            },
            # 系统设置类
            {
                "category": "⚙️ 系统设置",
                "category_en": "⚙️ System Settings",
                "icon": "🌅",
                "title": "主题切换",
                "title_en": "Theme Toggle",
                "content": "点击侧边栏底部的月亮/太阳图标切换深色/浅色主题",
                "content_en": "Click moon/sun icon at sidebar bottom to switch dark/light theme",
                "color": ModernColors.GRADIENT_MID,
            },
            {
                "category": "⚙️ 系统设置",
                "category_en": "⚙️ System Settings",
                "icon": "💻",
                "title": "低内存模式",
                "title_en": "Low Memory Mode",
                "content": "在设置中开启低内存模式，减少动画和日志缓存以节省内存",
                "content_en": "Enable Low Memory Mode in Settings to reduce animations and cache",
                "color": ModernColors.WARNING,
            },
            {
                "category": "⚙️ 系统设置",
                "category_en": "⚙️ System Settings",
                "icon": "📁",
                "title": "默认导出目录",
                "title_en": "Default Export Path",
                "content": "在设置中配置默认导出目录，不再每次选择保存位置",
                "content_en": "Set default export directory in Settings to skip folder selection",
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "⚙️ 系统设置",
                "category_en": "⚙️ System Settings",
                "icon": "📱",
                "title": "托盘模式",
                "title_en": "Tray Mode",
                "content": "开启「最小化到托盘」后，关闭窗口时程序会在后台运行",
                "content_en": 'Enable "Minimize to Tray" to keep app running when window is closed',
                "color": ModernColors.NEON_CYAN,
            },
            # 摘要技巧类
            {
                "category": "📝 摘要技巧",
                "category_en": "📝 Summary Tips",
                "icon": "🎯",
                "title": "选择摘要方法",
                "title_en": "Choose Summary Method",
                "content": "简单摘要适合快速概览，AI 摘要适合深度分析和关键观点提取",
                "content_en": "Simple summary for quick overview, AI summary for deep analysis",
                "color": ModernColors.GRADIENT_MID,
            },
            {
                "category": "📝 摘要技巧",
                "category_en": "📝 Summary Tips",
                "icon": "📋",
                "title": "查看关键要点",
                "title_en": "View Key Points",
                "content": "摘要结果中包含「关键要点」部分，快速了解文章核心内容",
                "content_en": 'Summary includes "Key Points" section for quick core content overview',
                "color": ModernColors.INFO,
            },
            {
                "category": "📝 摘要技巧",
                "category_en": "📝 Summary Tips",
                "icon": "⚙️",
                "title": "Ollama 本地服务",
                "title_en": "Ollama Local Service",
                "content": "安装 Ollama 后可使用本地 AI 模型，无需云端 API，完全离线工作",
                "content_en": "Install Ollama to use local AI models, no cloud API needed, fully offline",
                "color": ModernColors.SUCCESS,
            },
            # 链接处理类
            {
                "category": "🔗 链接处理",
                "category_en": "🔗 URL Processing",
                "icon": "✅",
                "title": "链接验证",
                "title_en": "URL Validation",
                "content": "输入链接时会实时验证格式，绿色勾表示有效链接",
                "content_en": "URLs are validated in real-time, green check means valid link",
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "🔗 链接处理",
                "category_en": "🔗 URL Processing",
                "icon": "📋",
                "title": "剪贴板检测",
                "title_en": "Clipboard Detection",
                "content": "复制微信链接后切换到程序，会自动识别并提示填入",
                "content_en": "Copy WeChat URL then switch to app, it auto-detects and prompts to paste",
                "color": ModernColors.INFO,
            },
            {
                "category": "🔗 链接处理",
                "category_en": "🔗 URL Processing",
                "icon": "📄",
                "title": "支持多种链接",
                "title_en": "Multiple URL Formats",
                "content": "支持标准微信文章链接和短链接，自动识别并处理",
                "content_en": "Supports standard WeChat article URLs and short links, auto-detected",
                "color": ModernColors.WARNING,
            },
            # 使用建议类
            {
                "category": "💡 使用建议",
                "category_en": "💡 Usage Tips",
                "icon": "📈",
                "title": "先测试单篇",
                "title_en": "Test Single First",
                "content": "建议先用单篇处理测试效果，确认满意后再批量处理",
                "content_en": "Test with single article first, then batch process after confirming results",
                "color": ModernColors.INFO,
            },
            {
                "category": "💡 使用建议",
                "category_en": "💡 Usage Tips",
                "icon": "📤",
                "title": "导出后核对",
                "title_en": "Review After Export",
                "content": "导出后建议打开文件核对内容，确保图片和格式正确",
                "content_en": "Review exported files to ensure images and formatting are correct",
                "color": ModernColors.WARNING,
            },
            {
                "category": "💡 使用建议",
                "category_en": "💡 Usage Tips",
                "icon": "🔒",
                "title": "API 密钥安全",
                "title_en": "API Key Security",
                "content": "API 密钥安全存储在本地，不会上传到任何服务器",
                "content_en": "API keys stored securely on local device, never uploaded to any server",
                "color": ModernColors.SUCCESS,
            },
            {
                "category": "💡 使用建议",
                "category_en": "💡 Usage Tips",
                "icon": "💾",
                "title": "定期备份",
                "title_en": "Regular Backup",
                "content": "重要文章建议导出备份，缓存数据可能会被清理",
                "content_en": "Export important articles as backup, cache data may be cleared",
                "color": ModernColors.WARNING,
            },
            # 常见问题类
            {
                "category": "❓ 常见问题",
                "category_en": "❓ FAQ",
                "icon": "🔍",
                "title": "文章加载失败",
                "title_en": "Article Load Failed",
                "content": "检查链接是否正确，部分文章可能已删除或需要登录查看",
                "content_en": "Check if URL is correct, some articles may be deleted or require login",
                "color": ModernColors.WARNING,
            },
            {
                "category": "❓ 常见问题",
                "category_en": "❓ FAQ",
                "icon": "🤖",
                "title": "AI 摘要失败",
                "title_en": "AI Summary Failed",
                "content": "检查 API 密钥是否正确，或服务是否可用，也可尝试其他摘要方法",
                "content_en": "Check API key or service availability, try other summary methods",
                "color": ModernColors.ERROR,
            },
            {
                "category": "❓ 常见问题",
                "category_en": "❓ FAQ",
                "icon": "📷",
                "title": "图片不显示",
                "title_en": "Images Not Showing",
                "content": "部分图片可能有防盗链保护，导出时会尝试下载并嵌入",
                "content_en": "Some images have hotlink protection, export will try to download and embed",
                "color": ModernColors.INFO,
            },
        ]

        self._current_tip_index = 0
        self._tip_auto_switch_id = None

        # 主容器
        tip_card = ctk.CTkFrame(
            parent,
            corner_radius=Spacing.RADIUS_LG,
            fg_color=(ModernColors.LIGHT_CARD, ModernColors.DARK_CARD),
            border_width=1,
            border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER),
        )
        tip_card.pack(fill="x", pady=20)

        # 内部容器
        inner = ctk.CTkFrame(tip_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)

        # 顶部：标题 + 导航按钮
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x")

        # 分类标签 (动态更新)
        self._tip_category_label = ctk.CTkLabel(
            header,
            text=self._tips_data[0]["category"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
        )
        self._tip_category_label.pack(side="left")

        # 导航按钮容器
        nav_frame = ctk.CTkFrame(header, fg_color="transparent")
        nav_frame.pack(side="right")

        # 上一条按钮
        prev_btn = ctk.CTkButton(
            nav_frame,
            text="‹",
            width=28,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            hover_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self._switch_tip(-1),
        )
        prev_btn.pack(side="left", padx=2)

        # 指示器 (如 1/8)
        self._tip_indicator_label = ctk.CTkLabel(
            nav_frame,
            text=f"1/{len(self._tips_data)}",
            font=ctk.CTkFont(size=11),
            text_color=(ModernColors.LIGHT_TEXT_MUTED, ModernColors.DARK_TEXT_MUTED),
        )
        self._tip_indicator_label.pack(side="left", padx=5)

        # 下一条按钮
        next_btn = ctk.CTkButton(
            nav_frame,
            text="›",
            width=28,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            hover_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: self._switch_tip(1),
        )
        next_btn.pack(side="left", padx=2)

        # 内容区域
        content_frame = ctk.CTkFrame(inner, fg_color="transparent")
        content_frame.pack(fill="x", pady=(12, 0))

        # 图标 + 标题
        title_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_row.pack(fill="x")

        self._tip_icon_label = ctk.CTkLabel(
            title_row, text=self._tips_data[0]["icon"], font=ctk.CTkFont(size=20)
        )
        self._tip_icon_label.pack(side="left")

        self._tip_title_label = ctk.CTkLabel(
            title_row,
            text=self._tips_data[0]["title"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
        )
        self._tip_title_label.pack(side="left", padx=(8, 0))

        # 颜色指示条
        self._tip_color_bar = ctk.CTkFrame(
            title_row, width=4, height=16, corner_radius=2, fg_color=self._tips_data[0]["color"]
        )
        self._tip_color_bar.pack(side="right")

        # 内容文本
        self._tip_content_label = ctk.CTkLabel(
            content_frame,
            text=self._tips_data[0]["content"],
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            justify="left",
            anchor="w",
        )
        self._tip_content_label.pack(fill="x", pady=(8, 0))

        # 底部：快捷跳转按钮
        actions_frame = ctk.CTkFrame(inner, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(15, 0))

        # 快捷按钮: (icon, 中文文本, 英文文本, 页面, 颜色)
        quick_actions = [
            ("📄", "单篇处理", "Single Article", self.PAGE_SINGLE, ModernColors.INFO),
            ("⚙️", "配置 API", "Configure API", self.PAGE_SETTINGS, ModernColors.GRADIENT_MID),
            ("📜", "历史记录", "History", self.PAGE_HISTORY, ModernColors.WARNING),
        ]

        is_en = get_i18n().get_language() != "zh_CN"
        for icon, text_zh, text_en, page, color in quick_actions:
            display_text = f"{icon} {text_en}" if is_en else f"{icon} {text_zh}"
            btn = ctk.CTkButton(
                actions_frame,
                text=display_text,
                font=ctk.CTkFont(size=11),
                height=28,
                corner_radius=Spacing.RADIUS_SM,
                fg_color="transparent",
                hover_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
                text_color=color,
                border_width=1,
                border_color=color,
                command=lambda p=page: self._navigate(p),
            )
            btn.pack(side="left", padx=(0, 8))

        # 启动自动轮播 (每 8 秒切换)
        self._start_tip_auto_switch()

        # 鼠标悬停时暂停轮播
        def on_enter(e):
            self._stop_tip_auto_switch()
            tip_card.configure(border_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT))

        def on_leave(e):
            self._start_tip_auto_switch()
            tip_card.configure(border_color=(ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER))

        tip_card.bind("<Enter>", on_enter)
        tip_card.bind("<Leave>", on_leave)
        for widget in [inner, header, content_frame, actions_frame, title_row]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    def _switch_tip(self, direction: int):
        """切换提示

        Args:
            direction: 1 下一条, -1 上一条
        """
        self._current_tip_index = (self._current_tip_index + direction) % len(self._tips_data)
        self._update_tip_display()

    def _update_tip_display(self):
        """更新提示显示"""
        tip = self._tips_data[self._current_tip_index]
        is_en = get_i18n().get_language() != "zh_CN"

        self._tip_category_label.configure(text=tip["category_en"] if is_en else tip["category"])
        self._tip_indicator_label.configure(
            text=f"{self._current_tip_index + 1}/{len(self._tips_data)}"
        )
        self._tip_icon_label.configure(text=tip["icon"])
        self._tip_title_label.configure(text=tip["title_en"] if is_en else tip["title"])
        self._tip_content_label.configure(text=tip["content_en"] if is_en else tip["content"])
        self._tip_color_bar.configure(fg_color=tip["color"])

    def _start_tip_auto_switch(self):
        """启动自动轮播"""
        if self._tip_auto_switch_id:
            return

        def auto_switch():
            self._switch_tip(1)
            self._tip_auto_switch_id = self.gui.root.after(8000, auto_switch)

        self._tip_auto_switch_id = self.gui.root.after(8000, auto_switch)

    def _stop_tip_auto_switch(self):
        """停止自动轮播"""
        if self._tip_auto_switch_id:
            self.gui.root.after_cancel(self._tip_auto_switch_id)
            self._tip_auto_switch_id = None
