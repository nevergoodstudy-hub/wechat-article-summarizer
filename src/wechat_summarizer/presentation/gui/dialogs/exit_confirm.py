"""退出确认对话框

现代化 CustomTkinter 风格的退出确认对话框：
- 支持暗色/亮色主题
- 模态对话框
- 显示当前运行任务信息
"""

from __future__ import annotations

import customtkinter as ctk

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing


class ExitConfirmDialog:
    """退出确认对话框 - 现代化 CustomTkinter 风格

    参考 CTkMessagebox 开源项目的设计规范：
    - 支持暗色/亮色主题
    - 带图标和自定义按钮
    - 模态对话框，防止用户误操作
    - 显示当前运行任务的详细信息
    """

    def __init__(
        self, parent, title: str, message: str, task_info: str | None = None, icon: str = "warning"
    ):
        """创建退出确认对话框

        Args:
            parent: 父窗口
            title: 对话框标题
            message: 主要提示信息
            task_info: 当前运行任务的详细信息
            icon: 图标类型 ('warning', 'question', 'info')
        """
        self.result = None

        # 创建对话框窗口
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("450x280")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()  # 模态

        # 居中显示
        self.dialog.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 450) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 280) // 2
        self.dialog.geometry(f"+{x}+{y}")

        # 主容器
        container = ctk.CTkFrame(self.dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # 图标和标题区域
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        # 图标
        icon_text = {"warning": "⚠️", "question": "❓", "info": "ℹ️"}.get(icon, "⚠️")
        icon_label = ctk.CTkLabel(header_frame, text=icon_text, font=ctk.CTkFont(size=36))
        icon_label.pack(side="left", padx=(10, 15))

        # 标题和消息
        text_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True)

        title_label = ctk.CTkLabel(
            text_frame, text=title, font=ctk.CTkFont(size=18, weight="bold"), anchor="w"
        )
        title_label.pack(fill="x")

        msg_label = ctk.CTkLabel(
            text_frame,
            text=message,
            font=ctk.CTkFont(size=13),
            text_color=(ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY),
            anchor="w",
            wraplength=320,
            justify="left",
        )
        msg_label.pack(fill="x", pady=(5, 0))

        # 任务信息区域（如果有）
        if task_info:
            task_frame = ctk.CTkFrame(
                container,
                corner_radius=Spacing.RADIUS_MD,
                fg_color=(ModernColors.WARNING_LIGHT, "#3d2e00"),
                border_width=1,
                border_color=(ModernColors.WARNING, "#5a4500"),
            )
            task_frame.pack(fill="x", pady=(0, 15))

            task_label = ctk.CTkLabel(
                task_frame,
                text=f"📝 当前任务: {task_info}",
                font=ctk.CTkFont(size=12),
                text_color=(ModernColors.WARNING, "#ffc107"),
                anchor="w",
                wraplength=380,
            )
            task_label.pack(fill="x", padx=15, pady=10)

        # 警告提示
        warning_label = ctk.CTkLabel(
            container,
            text="强制退出可能导致数据丢失或文件损坏",
            font=ctk.CTkFont(size=11),
            text_color=ModernColors.ERROR,
        )
        warning_label.pack(pady=(0, 15))

        # 按钮区域
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        # 取消按钮（继续任务）
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="继续任务",
            width=120,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.INFO,
            hover_color="#2563eb",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_cancel,
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        # 强制退出按钮
        exit_btn = ctk.CTkButton(
            btn_frame,
            text="强制退出",
            width=120,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.ERROR,
            hover_color="#dc2626",
            font=ctk.CTkFont(size=14),
            command=self._on_force_exit,
        )
        exit_btn.pack(side="right")

        # 等待到后台按钮
        wait_btn = ctk.CTkButton(
            btn_frame,
            text="后台运行",
            width=100,
            height=40,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=ModernColors.NEUTRAL_BTN,
            font=ctk.CTkFont(size=13),
            command=self._on_minimize,
        )
        wait_btn.pack(side="right", padx=(0, 10))

        # 绑定 ESC 键
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())

        # 绑定窗口关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # 等待对话框关闭
        self.dialog.wait_window()

    def _on_cancel(self):
        """取消/继续任务"""
        self.result = "cancel"
        self.dialog.destroy()

    def _on_force_exit(self):
        """强制退出"""
        self.result = "exit"
        self.dialog.destroy()

    def _on_minimize(self):
        """最小化到后台"""
        self.result = "minimize"
        self.dialog.destroy()

    def get(self) -> str:
        """获取结果

        Returns:
            'cancel': 用户选择继续任务
            'exit': 用户选择强制退出
            'minimize': 用户选择最小化到后台
        """
        return self.result or "cancel"
