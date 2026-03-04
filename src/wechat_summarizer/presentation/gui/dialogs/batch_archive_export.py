"""批量压缩导出对话框

支持文章选择和多格式压缩：
- 全选/反选
- ZIP、7z、RAR 格式
- 格式可用性检测
"""

from __future__ import annotations

from tkinter import filedialog, messagebox

import customtkinter as ctk

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing


class BatchArchiveExportDialog:
    """批量压缩导出对话框 - 支持文章选择和多格式压缩

    Features:
    - 支持选择要导出的文章（全选/反选）
    - 支持 ZIP、7z、RAR 三种压缩格式
    - 显示各格式的可用性状态
    - 模态对话框
    """

    def __init__(self, parent, articles: list, archive_exporter=None):
        """创建批量压缩导出对话框

        Args:
            parent: 父窗口
            articles: 文章列表
            archive_exporter: 多格式压缩导出器实例（用于检测格式可用性）
        """
        from ....infrastructure.adapters.exporters import MultiFormatArchiveExporter

        self.result = None  # {'articles': [...], 'format': 'zip', 'path': '...'}
        self.articles = articles
        self._archive_exporter = archive_exporter or MultiFormatArchiveExporter()
        self._format_infos = self._archive_exporter.get_available_formats()

        # 存储复选框变量
        self._article_vars: list[ctk.BooleanVar] = []

        # 创建对话框窗口
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("📦 批量压缩导出")

        # 根据文章数量调整窗口高度
        base_height = 480
        article_height = min(len(articles) * 35, 250)  # 每篇文章 35 像素，最多 250
        window_height = base_height + article_height
        self.dialog.geometry(f"550x{window_height}")
        self.dialog.resizable(False, True)
        self.dialog.transient(parent)
        self.dialog.grab_set()  # 模态

        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 550) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - window_height) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # 主容器
        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=15)

        # 标题
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header_frame, text="📦 批量压缩导出", font=ctk.CTkFont(size=20, weight="bold")
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text=f"共 {len(articles)} 篇文章",
            font=ctk.CTkFont(size=13),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(side="right")

        # ========== 文章选择区域 ==========
        article_section = ctk.CTkFrame(container, fg_color="transparent")
        article_section.pack(fill="both", expand=True, pady=(0, 10))

        # 文章选择标题栏
        article_header = ctk.CTkFrame(article_section, fg_color="transparent")
        article_header.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            article_header, text="📄 选择要导出的文章", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        # 全选/反选按钮
        btn_frame = ctk.CTkFrame(article_header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame,
            text="全选",
            width=60,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color=ModernColors.NEUTRAL_BTN,
            font=ctk.CTkFont(size=11),
            command=self._select_all,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_frame,
            text="反选",
            width=60,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color=ModernColors.NEUTRAL_BTN,
            font=ctk.CTkFont(size=11),
            command=self._toggle_selection,
        ).pack(side="left")

        # 文章列表（可滚动）
        self.article_list_frame = ctk.CTkScrollableFrame(
            article_section,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
            height=article_height,
        )
        self.article_list_frame.pack(fill="both", expand=True)

        # 添加文章复选框
        for i, article in enumerate(articles):
            var = ctk.BooleanVar(value=True)  # 默认全选
            self._article_vars.append(var)

            item_frame = ctk.CTkFrame(self.article_list_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)

            cb = ctk.CTkCheckBox(
                item_frame,
                text="",
                variable=var,
                width=20,
                checkbox_width=18,
                checkbox_height=18,
                corner_radius=Spacing.RADIUS_SM,
                command=self._update_selection_count,
            )
            cb.pack(side="left", padx=(5, 8))

            # 文章标题（截断显示）
            title_text = article.title[:45] + "..." if len(article.title) > 45 else article.title
            ctk.CTkLabel(
                item_frame, text=f"{i + 1}. {title_text}", font=ctk.CTkFont(size=12), anchor="w"
            ).pack(side="left", fill="x", expand=True)

        # 选中计数标签
        self.selection_count_label = ctk.CTkLabel(
            article_section,
            text=f"已选择 {len(articles)} 篇",
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.INFO,
        )
        self.selection_count_label.pack(anchor="w", pady=(5, 0))

        # ========== 格式选择区域 ==========
        format_section = ctk.CTkFrame(container, fg_color="transparent")
        format_section.pack(fill="x", pady=(10, 10))

        ctk.CTkLabel(
            format_section, text="📁 选择压缩格式", font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(0, 8))

        # 格式选项
        self._format_var = ctk.StringVar(value="zip")  # 默认 ZIP

        format_options_frame = ctk.CTkFrame(
            format_section,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_BG_SECONDARY, ModernColors.DARK_BG_SECONDARY),
        )
        format_options_frame.pack(fill="x")

        for info in self._format_infos:
            self._create_format_option(format_options_frame, info)

        # ========== 按钮区域 ==========
        btn_section = ctk.CTkFrame(container, fg_color="transparent")
        btn_section.pack(fill="x", pady=(15, 0))

        # 取消按钮
        ctk.CTkButton(
            btn_section,
            text="取消",
            width=100,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.NEUTRAL_BTN,
            font=ctk.CTkFont(size=14),
            command=self._on_cancel,
        ).pack(side="left")

        # 导出按钮
        self.export_btn = ctk.CTkButton(
            btn_section,
            text="📦 选择路径并导出",
            width=180,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.SUCCESS,
            hover_color="#059669",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_export,
        )
        self.export_btn.pack(side="right")

        # 绑定事件
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # 等待对话框关闭
        self.dialog.wait_window()

    def _create_format_option(self, parent, format_info):
        """创建格式选项"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=5)

        # 单选按钮
        rb = ctk.CTkRadioButton(
            frame,
            text="",
            variable=self._format_var,
            value=format_info.format.value,
            width=20,
            radiobutton_width=18,
            radiobutton_height=18,
            state="normal" if format_info.available else "disabled",
        )
        rb.pack(side="left", padx=(0, 8))

        # 格式名称和状态
        text_frame = ctk.CTkFrame(frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        # 状态图标 + 名称
        status_icon = "✓" if format_info.available else "✗"
        status_color = ModernColors.SUCCESS if format_info.available else ModernColors.ERROR

        name_frame = ctk.CTkFrame(text_frame, fg_color="transparent")
        name_frame.pack(fill="x")

        ctk.CTkLabel(
            name_frame,
            text=status_icon,
            font=ctk.CTkFont(size=12),
            text_color=status_color,
            width=20,
        ).pack(side="left")

        ctk.CTkLabel(
            name_frame,
            text=f"{format_info.name} ({format_info.extension})",
            font=ctk.CTkFont(size=13, weight="bold" if format_info.available else "normal"),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT)
            if format_info.available
            else ModernColors.NEUTRAL_BTN_DISABLED,
        ).pack(side="left", padx=(5, 0))

        # 原因说明
        ctk.CTkLabel(
            text_frame,
            text=format_info.reason,
            font=ctk.CTkFont(size=10),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
        ).pack(anchor="w", padx=(25, 0))

    def _select_all(self):
        """全选文章"""
        for var in self._article_vars:
            var.set(True)
        self._update_selection_count()

    def _toggle_selection(self):
        """反选文章"""
        for var in self._article_vars:
            var.set(not var.get())
        self._update_selection_count()

    def _update_selection_count(self):
        """更新选中计数"""
        count = sum(1 for var in self._article_vars if var.get())
        self.selection_count_label.configure(text=f"已选择 {count} 篇")

        # 如果没有选中任何文章，禁用导出按钮
        if count == 0:
            self.export_btn.configure(state="disabled")
        else:
            self.export_btn.configure(state="normal")

    def _on_cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def _on_export(self):
        """导出"""
        # 获取选中的文章
        selected_articles = [
            article
            for article, var in zip(self.articles, self._article_vars, strict=False)
            if var.get()
        ]

        if not selected_articles:
            messagebox.showwarning("提示", "请至少选择一篇文章")
            return

        # 获取选中的格式
        format_value = self._format_var.get()

        # 检查格式是否可用
        format_info = next((f for f in self._format_infos if f.format.value == format_value), None)
        if not format_info or not format_info.available:
            messagebox.showerror("错误", f"所选格式 {format_value} 不可用")
            return

        # 选择保存路径
        ext = format_info.extension
        filetypes = [(f"{format_info.name} 文件", f"*{ext}"), ("所有文件", "*.*")]

        path = filedialog.asksaveasfilename(
            defaultextension=ext,
            filetypes=filetypes,
            initialfile=f"articles_{len(selected_articles)}篇{ext}",
        )

        if not path:
            return  # 用户取消选择

        self.result = {"articles": selected_articles, "format": format_value, "path": path}
        self.dialog.destroy()

    def get(self):
        """获取结果

        Returns:
            dict: {'articles': [...], 'format': 'zip'/'7z'/'rar', 'path': '...'}
            None: 用户取消
        """
        return self.result
