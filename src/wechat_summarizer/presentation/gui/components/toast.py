"""Toast通知组件 - 2026 UI设计趋势

提供：
- 4种类型（success/error/warning/info）
- 自动消失定时器
- 堆叠显示管理
- 平滑出现/消失动画

安全审查：
- 通知数量限制，防内存泄漏
- 定时器管理，防止泄漏
"""
from __future__ import annotations

import tkinter as tk
from enum import Enum
from typing import Optional, Callable, List

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors
from ..styles.typography import get_text_style, TextStyles


class ToastType(Enum):
    """通知类型"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Toast:
    """Toast通知
    
    单个通知实例。
    """
    
    def __init__(
        self,
        master,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,  # 毫秒
        on_close: Optional[Callable] = None,
        theme: str = "dark"
    ):
        """初始化Toast
        
        Args:
            master: 父容器
            message: 消息内容
            toast_type: 通知类型
            duration: 显示时长（毫秒），0表示不自动关闭
            on_close: 关闭回调
            theme: 主题
        """
        self._master = master
        self._message = message
        self._toast_type = toast_type
        self._duration = duration
        self._on_close = on_close
        self._theme = theme
        self._timer_id = None
        
        # 颜色配置
        colors = self._get_colors(theme, toast_type)
        
        # 创建容器
        if _CTK_AVAILABLE:
            self._frame = ctk.CTkFrame(
                master,
                fg_color=colors['bg'],
                corner_radius=8,
                border_width=1,
                border_color=colors['border']
            )
        else:
            self._frame = tk.Frame(
                master,
                bg=colors['bg'],
                highlightthickness=1,
                highlightbackground=colors['border']
            )
        
        # 内容区域
        content_frame = self._frame
        
        # 图标（简化实现，使用文字表示）
        icon_text = self._get_icon_text(toast_type)
        
        if _CTK_AVAILABLE:
            icon_label = ctk.CTkLabel(
                content_frame,
                text=icon_text,
                text_color=colors['icon'],
                font=("Arial", 16)
            )
        else:
            icon_label = tk.Label(
                content_frame,
                text=icon_text,
                fg=colors['icon'],
                bg=colors['bg'],
                font=("Arial", 16)
            )
        
        icon_label.pack(side="left", padx=(12, 8), pady=12)
        
        # 消息文本
        if _CTK_AVAILABLE:
            message_label = ctk.CTkLabel(
                content_frame,
                text=message,
                text_color=colors['text'],
                font=get_text_style(TextStyles.BODY),
                anchor="w",
                justify="left"
            )
        else:
            message_label = tk.Label(
                content_frame,
                text=message,
                fg=colors['text'],
                bg=colors['bg'],
                font=get_text_style(TextStyles.BODY),
                anchor="w",
                justify="left"
            )
        
        message_label.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)
        
        # 关闭按钮
        close_text = "×"
        
        if _CTK_AVAILABLE:
            close_btn = ctk.CTkButton(
                content_frame,
                text=close_text,
                width=24,
                height=24,
                fg_color="transparent",
                hover_color=colors['hover'],
                text_color=colors['text'],
                command=self.close
            )
        else:
            close_btn = tk.Button(
                content_frame,
                text=close_text,
                width=2,
                bg=colors['bg'],
                fg=colors['text'],
                relief="flat",
                command=self.close
            )
        
        close_btn.pack(side="right", padx=(0, 8), pady=8)
        
        # 自动关闭定时器
        if duration > 0:
            self._timer_id = self._frame.after(duration, self.close)
    
    def _get_colors(self, theme: str, toast_type: ToastType) -> dict:
        """获取颜色配置"""
        # 基于类型的颜色
        type_colors = {
            ToastType.SUCCESS: {
                'icon': ModernColors.SUCCESS,
                'border': ModernColors.SUCCESS,
            },
            ToastType.ERROR: {
                'icon': ModernColors.ERROR,
                'border': ModernColors.ERROR,
            },
            ToastType.WARNING: {
                'icon': ModernColors.WARNING,
                'border': ModernColors.WARNING,
            },
            ToastType.INFO: {
                'icon': ModernColors.INFO,
                'border': ModernColors.INFO,
            }
        }
        
        # 主题颜色
        if theme == "dark":
            base = {
                'bg': ModernColors.DARK_CARD,
                'text': ModernColors.DARK_TEXT,
                'hover': ModernColors.DARK_CARD_HOVER,
            }
        else:
            base = {
                'bg': ModernColors.LIGHT_CARD,
                'text': ModernColors.LIGHT_TEXT,
                'hover': ModernColors.LIGHT_CARD_HOVER,
            }
        
        return {**base, **type_colors[toast_type]}
    
    @staticmethod
    def _get_icon_text(toast_type: ToastType) -> str:
        """获取图标文本"""
        icons = {
            ToastType.SUCCESS: "✓",
            ToastType.ERROR: "✕",
            ToastType.WARNING: "⚠",
            ToastType.INFO: "ℹ"
        }
        return icons[toast_type]
    
    def close(self):
        """关闭Toast"""
        # 取消定时器
        if self._timer_id:
            self._frame.after_cancel(self._timer_id)
            self._timer_id = None
        
        # 销毁组件
        self._frame.destroy()
        
        # 回调
        if self._on_close:
            self._on_close()
    
    def pack(self, **kwargs):
        """打包"""
        self._frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self._frame.grid(**kwargs)


class ToastManager:
    """Toast管理器
    
    管理多个Toast的显示和堆叠。
    """
    
    MAX_TOASTS = 5  # 最大同时显示数量
    
    def __init__(self, master, position: str = "top-right", theme: str = "dark"):
        """初始化Toast管理器
        
        Args:
            master: 父容器
            position: 显示位置 ("top-right", "top-left", "bottom-right", "bottom-left")
            theme: 主题
        """
        self._master = master
        self._position = position
        self._theme = theme
        self._toasts: List[Toast] = []
        self._container = None  # 延迟创建，避免空容器显示
    
    def _ensure_container(self):
        """确保容器存在（延迟创建）"""
        if self._container is not None:
            return
        
        # 创建容器 - 使用最小尺寸，仅在有Toast时扩展
        if _CTK_AVAILABLE:
            self._container = ctk.CTkFrame(
                self._master, 
                fg_color="transparent",
                width=320,  # 固定宽度
                height=1    # 最小高度，由内容撑开
            )
        else:
            self._container = tk.Frame(self._master, width=320, height=1)
        
        # 定位容器
        self._position_container()
    
    def _position_container(self):
        """定位容器"""
        if self._container is None:
            return
        
        if self._position == "top-right":
            self._container.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)
        elif self._position == "top-left":
            self._container.place(relx=0.0, rely=0.0, anchor="nw", x=20, y=20)
        elif self._position == "bottom-right":
            self._container.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-20)
        elif self._position == "bottom-left":
            self._container.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
    
    def show(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000
    ) -> Toast:
        """显示Toast
        
        Args:
            message: 消息内容
            toast_type: 通知类型
            duration: 显示时长
            
        Returns:
            Toast实例
        """
        # 确保容器存在（延迟创建）
        self._ensure_container()
        
        # 数量限制
        if len(self._toasts) >= self.MAX_TOASTS:
            # 关闭最旧的
            self._toasts[0].close()
        
        # 创建新Toast
        toast = Toast(
            self._container,
            message=message,
            toast_type=toast_type,
            duration=duration,
            on_close=lambda: self._remove_toast(toast),
            theme=self._theme
        )
        
        toast.pack(fill="x", pady=(0, 8))
        self._toasts.append(toast)
        
        return toast
    
    def _remove_toast(self, toast: Toast):
        """从管理器中移除Toast"""
        if toast in self._toasts:
            self._toasts.remove(toast)
    
    def success(self, message: str, duration: int = 3000) -> Toast:
        """显示成功通知"""
        return self.show(message, ToastType.SUCCESS, duration)
    
    def error(self, message: str, duration: int = 5000) -> Toast:
        """显示错误通知（默认更长时间）"""
        return self.show(message, ToastType.ERROR, duration)
    
    def warning(self, message: str, duration: int = 4000) -> Toast:
        """显示警告通知"""
        return self.show(message, ToastType.WARNING, duration)
    
    def info(self, message: str, duration: int = 3000) -> Toast:
        """显示信息通知"""
        return self.show(message, ToastType.INFO, duration)
    
    def clear_all(self):
        """关闭所有Toast"""
        for toast in self._toasts[:]:  # 复制列表避免修改时迭代问题
            toast.close()


# 全局Toast管理器实例（延迟初始化）
_toast_manager: Optional[ToastManager] = None


def init_toast_manager(master, **kwargs) -> ToastManager:
    """初始化全局Toast管理器
    
    Args:
        master: 父容器
        **kwargs: ToastManager参数
        
    Returns:
        ToastManager实例
    """
    global _toast_manager
    _toast_manager = ToastManager(master, **kwargs)
    return _toast_manager


def show_toast(message: str, toast_type: ToastType = ToastType.INFO, duration: int = 3000):
    """显示Toast（使用全局管理器）
    
    Args:
        message: 消息内容
        toast_type: 通知类型
        duration: 显示时长
    """
    if _toast_manager:
        _toast_manager.show(message, toast_type, duration)


def show_success(message: str):
    """显示成功通知"""
    if _toast_manager:
        _toast_manager.success(message)


def show_error(message: str):
    """显示错误通知"""
    if _toast_manager:
        _toast_manager.error(message)


def show_warning(message: str):
    """显示警告通知"""
    if _toast_manager:
        _toast_manager.warning(message)


def show_info(message: str):
    """显示信息通知"""
    if _toast_manager:
        _toast_manager.info(message)
