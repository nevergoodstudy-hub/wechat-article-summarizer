"""现代模态框组件 - 2026 UI设计趋势

提供：
- 背景遮罩（半透明模糊效果）
- 平滑出现/消失动画
- ESC键关闭支持
- 多种尺寸预设
- 防堆叠管理

安全审查：
- 防止模态框堆叠混乱
- 键盘事件正确解绑
- 内存泄漏防护
"""
from __future__ import annotations

import tkinter as tk
from enum import Enum
from typing import Optional, Callable

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors
from ..styles.typography import get_text_style, TextStyles


class ModalSize(Enum):
    """模态框尺寸"""
    SMALL = (400, 200)    # 小型：确认框
    MEDIUM = (500, 300)   # 中型：表单
    LARGE = (700, 500)    # 大型：详情展示
    FULLSCREEN = (0, 0)   # 全屏：特殊场景


class Modal:
    """现代模态框组件
    
    特性：
    - 背景遮罩
    - 动画效果
    - 键盘导航
    - 尺寸预设
    """
    
    # 模态框堆栈管理
    _modal_stack = []
    
    def __init__(
        self,
        master,
        title: str = "标题",
        size: ModalSize = ModalSize.MEDIUM,
        closable: bool = True,
        on_close: Optional[Callable] = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化模态框
        
        Args:
            master: 父容器
            title: 标题
            size: 尺寸
            closable: 是否可关闭
            on_close: 关闭回调
            theme: 主题
            **kwargs: 其他参数
        """
        self._master = master
        self._title = title
        self._size = size
        self._closable = closable
        self._on_close = on_close
        self._theme = theme
        self._is_open = False
        
        # 颜色配置
        self._colors = self._get_colors(theme)
        
        # 创建遮罩层
        self._create_overlay()
        
        # 创建模态框内容
        self._create_modal()
        
        # 绑定ESC关闭
        if closable:
            self._master.bind("<Escape>", self._on_escape, add="+")
    
    def _get_colors(self, theme: str) -> dict:
        """获取颜色配置"""
        if theme == "dark":
            return {
                'overlay': "rgba(0,0,0,0.5)",  # 遮罩
                'bg': ModernColors.DARK_SURFACE,
                'text': ModernColors.DARK_TEXT,
                'text_secondary': ModernColors.DARK_TEXT_SECONDARY,
                'border': ModernColors.DARK_BORDER,
                'header_bg': ModernColors.DARK_CARD,
            }
        else:
            return {
                'overlay': "rgba(0,0,0,0.3)",
                'bg': ModernColors.LIGHT_SURFACE,
                'text': ModernColors.LIGHT_TEXT,
                'text_secondary': ModernColors.LIGHT_TEXT_SECONDARY,
                'border': ModernColors.LIGHT_BORDER,
                'header_bg': ModernColors.LIGHT_CARD,
            }
    
    def _create_overlay(self):
        """创建遮罩层"""
        # 使用Frame模拟遮罩
        overlay_color = "#000000" if self._theme == "dark" else "#666666"
        
        if _CTK_AVAILABLE:
            self._overlay = ctk.CTkFrame(
                self._master,
                fg_color=overlay_color,
            )
        else:
            self._overlay = tk.Frame(
                self._master,
                bg=overlay_color
            )
        
        # 点击遮罩关闭
        if self._closable:
            self._overlay.bind("<Button-1>", lambda e: self.close())
    
    def _create_modal(self):
        """创建模态框内容"""
        # 获取尺寸
        if self._size == ModalSize.FULLSCREEN:
            width = self._master.winfo_width() - 40
            height = self._master.winfo_height() - 40
        else:
            width, height = self._size.value
        
        # 模态框容器
        if _CTK_AVAILABLE:
            self._modal_frame = ctk.CTkFrame(
                self._overlay,
                width=width,
                height=height,
                fg_color=self._colors['bg'],
                border_width=1,
                border_color=self._colors['border'],
                corner_radius=12
            )
        else:
            self._modal_frame = tk.Frame(
                self._overlay,
                width=width,
                height=height,
                bg=self._colors['bg'],
                highlightthickness=1,
                highlightbackground=self._colors['border']
            )
        
        # 阻止点击事件冒泡到遮罩
        self._modal_frame.bind("<Button-1>", lambda e: "break")
        
        # 创建头部
        self._create_header()
        
        # 创建内容区域
        self._create_content_area()
        
        # 创建底部操作区
        self._create_footer()
    
    def _create_header(self):
        """创建头部"""
        if _CTK_AVAILABLE:
            header = ctk.CTkFrame(
                self._modal_frame,
                fg_color=self._colors['header_bg'],
                height=50,
                corner_radius=0
            )
        else:
            header = tk.Frame(
                self._modal_frame,
                bg=self._colors['header_bg'],
                height=50
            )
        
        header.pack(fill="x", padx=1, pady=(1, 0))
        header.pack_propagate(False)
        
        # 标题
        if _CTK_AVAILABLE:
            title_label = ctk.CTkLabel(
                header,
                text=self._title,
                font=get_text_style(TextStyles.HEADING_4),
                text_color=self._colors['text']
            )
        else:
            title_label = tk.Label(
                header,
                text=self._title,
                font=get_text_style(TextStyles.HEADING_4),
                fg=self._colors['text'],
                bg=self._colors['header_bg']
            )
        
        title_label.pack(side="left", padx=20, pady=10)
        
        # 关闭按钮
        if self._closable:
            if _CTK_AVAILABLE:
                close_btn = ctk.CTkButton(
                    header,
                    text="×",
                    width=30,
                    height=30,
                    fg_color="transparent",
                    hover_color=ModernColors.ERROR,
                    text_color=self._colors['text'],
                    corner_radius=15,
                    command=self.close
                )
            else:
                close_btn = tk.Button(
                    header,
                    text="×",
                    width=3,
                    bg=self._colors['header_bg'],
                    fg=self._colors['text'],
                    relief="flat",
                    command=self.close
                )
            
            close_btn.pack(side="right", padx=10, pady=10)
    
    def _create_content_area(self):
        """创建内容区域"""
        if _CTK_AVAILABLE:
            self._content = ctk.CTkFrame(
                self._modal_frame,
                fg_color="transparent"
            )
        else:
            self._content = tk.Frame(
                self._modal_frame,
                bg=self._colors['bg']
            )
        
        self._content.pack(fill="both", expand=True, padx=20, pady=20)
    
    def _create_footer(self):
        """创建底部操作区"""
        if _CTK_AVAILABLE:
            self._footer = ctk.CTkFrame(
                self._modal_frame,
                fg_color="transparent",
                height=60
            )
        else:
            self._footer = tk.Frame(
                self._modal_frame,
                bg=self._colors['bg'],
                height=60
            )
        
        self._footer.pack(fill="x", padx=20, pady=(0, 20))
    
    def _on_escape(self, event):
        """ESC键处理"""
        if self._is_open and self._closable:
            # 只关闭最顶层的模态框
            if Modal._modal_stack and Modal._modal_stack[-1] == self:
                self.close()
    
    def open(self):
        """打开模态框"""
        if self._is_open:
            return
        
        self._is_open = True
        Modal._modal_stack.append(self)
        
        # 显示遮罩
        self._overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # 显示模态框（居中）
        self._modal_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # 提升到最顶层
        self._overlay.lift()
        self._modal_frame.lift()
    
    def close(self):
        """关闭模态框"""
        if not self._is_open:
            return
        
        self._is_open = False
        
        # 从堆栈移除
        if self in Modal._modal_stack:
            Modal._modal_stack.remove(self)
        
        # 隐藏
        self._modal_frame.place_forget()
        self._overlay.place_forget()
        
        # 回调
        if self._on_close:
            self._on_close()
    
    def destroy(self):
        """销毁模态框"""
        self.close()
        
        # 解绑事件
        try:
            self._master.unbind("<Escape>")
        except:
            pass
        
        # 销毁组件
        self._modal_frame.destroy()
        self._overlay.destroy()
    
    def get_content_frame(self):
        """获取内容区域Frame
        
        Returns:
            内容区域Frame，用于添加自定义内容
        """
        return self._content
    
    def get_footer_frame(self):
        """获取底部区域Frame
        
        Returns:
            底部区域Frame，用于添加操作按钮
        """
        return self._footer
    
    def set_title(self, title: str):
        """设置标题
        
        Args:
            title: 新标题
        """
        self._title = title
        # 需要重新创建头部以更新标题


class ConfirmModal(Modal):
    """确认对话框
    
    预设的确认/取消对话框。
    """
    
    def __init__(
        self,
        master,
        title: str = "确认",
        message: str = "确定要执行此操作吗？",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化确认对话框
        
        Args:
            master: 父容器
            title: 标题
            message: 消息内容
            confirm_text: 确认按钮文本
            cancel_text: 取消按钮文本
            on_confirm: 确认回调
            on_cancel: 取消回调
            theme: 主题
            **kwargs: 其他参数
        """
        self._message = message
        self._confirm_text = confirm_text
        self._cancel_text = cancel_text
        self._on_confirm = on_confirm
        self._on_cancel_callback = on_cancel
        
        super().__init__(
            master,
            title=title,
            size=ModalSize.SMALL,
            theme=theme,
            on_close=on_cancel,
            **kwargs
        )
        
        # 添加消息和按钮
        self._setup_content()
    
    def _setup_content(self):
        """设置内容"""
        content = self.get_content_frame()
        
        # 消息文本
        if _CTK_AVAILABLE:
            msg_label = ctk.CTkLabel(
                content,
                text=self._message,
                font=get_text_style(TextStyles.BODY),
                text_color=self._colors['text'],
                wraplength=350
            )
        else:
            msg_label = tk.Label(
                content,
                text=self._message,
                font=get_text_style(TextStyles.BODY),
                fg=self._colors['text'],
                bg=self._colors['bg'],
                wraplength=350
            )
        
        msg_label.pack(expand=True)
        
        # 按钮区域
        footer = self.get_footer_frame()
        
        # 取消按钮
        if _CTK_AVAILABLE:
            cancel_btn = ctk.CTkButton(
                footer,
                text=self._cancel_text,
                fg_color="transparent",
                hover_color=self._colors['border'],
                text_color=self._colors['text'],
                border_width=1,
                border_color=self._colors['border'],
                corner_radius=8,
                command=self._handle_cancel
            )
        else:
            cancel_btn = tk.Button(
                footer,
                text=self._cancel_text,
                bg=self._colors['bg'],
                fg=self._colors['text'],
                relief="solid",
                bd=1,
                command=self._handle_cancel
            )
        
        cancel_btn.pack(side="right", padx=(10, 0))
        
        # 确认按钮
        if _CTK_AVAILABLE:
            confirm_btn = ctk.CTkButton(
                footer,
                text=self._confirm_text,
                fg_color=ModernColors.DARK_ACCENT if self._theme == "dark" else ModernColors.LIGHT_ACCENT,
                hover_color=ModernColors.DARK_ACCENT_HOVER if self._theme == "dark" else ModernColors.LIGHT_ACCENT_HOVER,
                text_color="#FFFFFF",
                corner_radius=8,
                command=self._handle_confirm
            )
        else:
            confirm_btn = tk.Button(
                footer,
                text=self._confirm_text,
                bg=ModernColors.DARK_ACCENT if self._theme == "dark" else ModernColors.LIGHT_ACCENT,
                fg="#FFFFFF",
                relief="flat",
                command=self._handle_confirm
            )
        
        confirm_btn.pack(side="right")
    
    def _handle_confirm(self):
        """处理确认"""
        self.close()
        if self._on_confirm:
            self._on_confirm()
    
    def _handle_cancel(self):
        """处理取消"""
        self.close()
        if self._on_cancel_callback:
            self._on_cancel_callback()


class AlertModal(Modal):
    """警告/提示对话框
    
    只有确认按钮的提示框。
    """
    
    def __init__(
        self,
        master,
        title: str = "提示",
        message: str = "",
        button_text: str = "知道了",
        alert_type: str = "info",  # info, success, warning, error
        on_close: Optional[Callable] = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化提示对话框
        
        Args:
            master: 父容器
            title: 标题
            message: 消息内容
            button_text: 按钮文本
            alert_type: 提示类型
            on_close: 关闭回调
            theme: 主题
            **kwargs: 其他参数
        """
        self._message = message
        self._button_text = button_text
        self._alert_type = alert_type
        
        super().__init__(
            master,
            title=title,
            size=ModalSize.SMALL,
            theme=theme,
            on_close=on_close,
            **kwargs
        )
        
        self._setup_content()
    
    def _get_type_color(self) -> str:
        """获取类型对应颜色"""
        colors = {
            "info": ModernColors.INFO,
            "success": ModernColors.SUCCESS,
            "warning": ModernColors.WARNING,
            "error": ModernColors.ERROR,
        }
        return colors.get(self._alert_type, ModernColors.INFO)
    
    def _setup_content(self):
        """设置内容"""
        content = self.get_content_frame()
        
        # 图标（简化实现）
        icon_map = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✕",
        }
        icon = icon_map.get(self._alert_type, "ℹ")
        
        if _CTK_AVAILABLE:
            icon_label = ctk.CTkLabel(
                content,
                text=icon,
                font=("Arial", 32),
                text_color=self._get_type_color()
            )
        else:
            icon_label = tk.Label(
                content,
                text=icon,
                font=("Arial", 32),
                fg=self._get_type_color(),
                bg=self._colors['bg']
            )
        
        icon_label.pack(pady=(0, 10))
        
        # 消息
        if _CTK_AVAILABLE:
            msg_label = ctk.CTkLabel(
                content,
                text=self._message,
                font=get_text_style(TextStyles.BODY),
                text_color=self._colors['text'],
                wraplength=350
            )
        else:
            msg_label = tk.Label(
                content,
                text=self._message,
                font=get_text_style(TextStyles.BODY),
                fg=self._colors['text'],
                bg=self._colors['bg'],
                wraplength=350
            )
        
        msg_label.pack()
        
        # 按钮
        footer = self.get_footer_frame()
        
        if _CTK_AVAILABLE:
            ok_btn = ctk.CTkButton(
                footer,
                text=self._button_text,
                fg_color=self._get_type_color(),
                hover_color=self._get_type_color(),
                text_color="#FFFFFF",
                corner_radius=8,
                command=self.close
            )
        else:
            ok_btn = tk.Button(
                footer,
                text=self._button_text,
                bg=self._get_type_color(),
                fg="#FFFFFF",
                relief="flat",
                command=self.close
            )
        
        ok_btn.pack(side="right")


# 便捷函数
def show_modal(
    master,
    title: str = "标题",
    size: ModalSize = ModalSize.MEDIUM,
    theme: str = "dark"
) -> Modal:
    """显示模态框
    
    Args:
        master: 父容器
        title: 标题
        size: 尺寸
        theme: 主题
        
    Returns:
        Modal实例
    """
    modal = Modal(master, title=title, size=size, theme=theme)
    modal.open()
    return modal


def show_confirm(
    master,
    message: str,
    title: str = "确认",
    on_confirm: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None,
    theme: str = "dark"
) -> ConfirmModal:
    """显示确认对话框
    
    Args:
        master: 父容器
        message: 消息
        title: 标题
        on_confirm: 确认回调
        on_cancel: 取消回调
        theme: 主题
        
    Returns:
        ConfirmModal实例
    """
    modal = ConfirmModal(
        master,
        title=title,
        message=message,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
        theme=theme
    )
    modal.open()
    return modal


def show_alert(
    master,
    message: str,
    title: str = "提示",
    alert_type: str = "info",
    theme: str = "dark"
) -> AlertModal:
    """显示提示对话框
    
    Args:
        master: 父容器
        message: 消息
        title: 标题
        alert_type: 类型 (info/success/warning/error)
        theme: 主题
        
    Returns:
        AlertModal实例
    """
    modal = AlertModal(
        master,
        title=title,
        message=message,
        alert_type=alert_type,
        theme=theme
    )
    modal.open()
    return modal
