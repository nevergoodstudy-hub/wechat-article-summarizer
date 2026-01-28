"""进度指示器组件 - 2026 UI设计趋势

提供：
- 线性进度条
- 圆形进度条
- 不确定状态脉冲动画
- 步骤进度器

安全审查：
- 动画性能优化
- 进度值边界检查
"""
from __future__ import annotations

import tkinter as tk
from enum import Enum
from typing import Optional, List, Union

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors


class LinearProgress(ctk.CTkProgressBar if _CTK_AVAILABLE else tk.Canvas):
    """线性进度条
    
    支持确定和不确定状态。
    """
    
    def __init__(
        self,
        master,
        width: int = 300,
        height: int = 4,
        indeterminate: bool = False,
        theme: str = "dark",
        corner_radius: Optional[int] = None,
        **kwargs
    ):
        """初始化线性进度条
        
        Args:
            master: 父容器
            width: 宽度
            height: 高度
            indeterminate: 是否不确定状态
            theme: 主题
            corner_radius: 圆角半径 (默认为高度的一半)
            **kwargs: 其他参数
        """
        self._width = width
        self._height = height
        self._indeterminate = indeterminate
        self._theme = theme
        self._progress = 0.0
        
        # 圆角半径默认值
        if corner_radius is None:
            corner_radius = height // 2
        
        # 颜色
        if theme == "dark":
            bg_color = ModernColors.DARK_CARD
            fg_color = ModernColors.DARK_ACCENT
        else:
            bg_color = ModernColors.LIGHT_CARD
            fg_color = ModernColors.LIGHT_ACCENT
        
        # 初始化父类
        if _CTK_AVAILABLE:
            super().__init__(
                master,
                width=width,
                height=height,
                fg_color=bg_color,
                progress_color=fg_color,
                corner_radius=corner_radius,
                **kwargs
            )
            
            if indeterminate:
                self.configure(mode="indeterminate")
                self.start()
            else:
                self.set(0)
        else:
            # Tkinter canvas实现
            super().__init__(
                master,
                width=width,
                height=height,
                bg=bg_color,
                highlightthickness=0,
                **kwargs
            )
            
            # 绘制背景
            self.create_rectangle(
                0, 0, width, height,
                fill=bg_color,
                outline=""
            )
            
            # 进度条
            self._progress_rect = self.create_rectangle(
                0, 0, 0, height,
                fill=fg_color,
                outline=""
            )
    
    def set(self, value: float):
        """设置进度值
        
        Args:
            value: 进度值 (0.0-1.0)
        """
        # 边界检查
        value = max(0.0, min(1.0, value))
        self._progress = value
        
        if _CTK_AVAILABLE:
            super().set(value)
        else:
            # 更新canvas
            progress_width = int(self._width * value)
            self.coords(self._progress_rect, 0, 0, progress_width, self._height)
    
    def get(self) -> float:
        """获取进度值
        
        Returns:
            当前进度 (0.0-1.0)
        """
        if _CTK_AVAILABLE:
            return super().get()
        else:
            return self._progress


class CircularProgress:
    """圆形进度条
    
    使用Canvas绘制圆形进度指示器。
    """
    
    def __init__(
        self,
        master,
        size: int = 100,
        width: int = 8,
        indeterminate: bool = False,
        theme: str = "dark"
    ):
        """初始化圆形进度条
        
        Args:
            master: 父容器
            size: 尺寸
            width: 线宽
            indeterminate: 是否不确定状态
            theme: 主题
        """
        self._size = size
        self._width = width
        self._indeterminate = indeterminate
        self._theme = theme
        self._progress = 0.0
        self._animation_angle = 0
        
        # 颜色
        if theme == "dark":
            bg_color = ModernColors.DARK_BACKGROUND
            fg_color = ModernColors.DARK_ACCENT
            track_color = ModernColors.DARK_CARD
        else:
            bg_color = ModernColors.LIGHT_BACKGROUND
            fg_color = ModernColors.LIGHT_ACCENT
            track_color = ModernColors.LIGHT_CARD
        
        # Canvas
        self._canvas = tk.Canvas(
            master,
            width=size,
            height=size,
            bg=bg_color,
            highlightthickness=0
        )
        
        # 绘制轨道圆圈
        padding = width
        self._canvas.create_oval(
            padding, padding,
            size - padding, size - padding,
            outline=track_color,
            width=width
        )
        
        # 进度弧
        self._progress_arc = self._canvas.create_arc(
            padding, padding,
            size - padding, size - padding,
            start=90,
            extent=0,
            outline=fg_color,
            width=width,
            style=tk.ARC
        )
        
        if indeterminate:
            self._animate()
    
    def set(self, value: float):
        """设置进度值
        
        Args:
            value: 进度值 (0.0-1.0)
        """
        value = max(0.0, min(1.0, value))
        self._progress = value
        
        # 更新弧度（360度 * 进度）
        extent = -360 * value
        self._canvas.itemconfig(self._progress_arc, extent=extent)
    
    def get(self) -> float:
        """获取进度值"""
        return self._progress
    
    def _animate(self):
        """不确定状态动画"""
        if not self._indeterminate:
            return
        
        self._animation_angle = (self._animation_angle + 5) % 360
        self._canvas.itemconfig(
            self._progress_arc,
            start=self._animation_angle,
            extent=-90
        )
        
        self._canvas.after(16, self._animate)  # ~60fps
    
    def pack(self, **kwargs):
        """打包"""
        self._canvas.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self._canvas.grid(**kwargs)


class StepProgress:
    """步骤进度器
    
    显示多步骤流程的进度。
    """
    
    def __init__(
        self,
        master,
        steps: List[str],
        theme: str = "dark"
    ):
        """初始化步骤进度器
        
        Args:
            master: 父容器
            steps: 步骤列表
            theme: 主题
        """
        self._steps = steps
        self._current_step = 0
        self._theme = theme
        
        # 容器
        if _CTK_AVAILABLE:
            self._container = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._container = tk.Frame(master)
        
        # 颜色
        if theme == "dark":
            active_color = ModernColors.DARK_ACCENT
            inactive_color = ModernColors.DARK_BORDER
            text_color = ModernColors.DARK_TEXT
            text_inactive = ModernColors.DARK_TEXT_SECONDARY
        else:
            active_color = ModernColors.LIGHT_ACCENT
            inactive_color = ModernColors.LIGHT_BORDER
            text_color = ModernColors.LIGHT_TEXT
            text_inactive = ModernColors.LIGHT_TEXT_SECONDARY
        
        self._colors = {
            'active': active_color,
            'inactive': inactive_color,
            'text': text_color,
            'text_inactive': text_inactive
        }
        
        # 创建步骤指示器
        self._step_widgets = []
        self._create_steps()
    
    def _create_steps(self):
        """创建步骤UI"""
        for i, step_name in enumerate(self._steps):
            # 步骤容器
            if _CTK_AVAILABLE:
                step_frame = ctk.CTkFrame(self._container, fg_color="transparent")
            else:
                step_frame = tk.Frame(self._container)
            
            step_frame.pack(side="left", padx=10)
            
            # 圆圈指示器
            is_active = i == self._current_step
            color = self._colors['active'] if is_active else self._colors['inactive']
            
            indicator = tk.Canvas(
                step_frame,
                width=32,
                height=32,
                bg=self._colors['active'] if i < self._current_step else 'transparent',
                highlightthickness=0
            )
            indicator.pack()
            
            # 绘制圆圈
            if i < self._current_step:
                # 已完成 - 填充圆
                indicator.create_oval(
                    4, 4, 28, 28,
                    fill=color,
                    outline=""
                )
                # 勾号
                indicator.create_line(
                    10, 16, 14, 20,
                    fill="white",
                    width=2
                )
                indicator.create_line(
                    14, 20, 22, 10,
                    fill="white",
                    width=2
                )
            elif i == self._current_step:
                # 当前步骤 - 实心圆
                indicator.create_oval(
                    4, 4, 28, 28,
                    fill=color,
                    outline=""
                )
            else:
                # 未完成 - 空心圆
                indicator.create_oval(
                    4, 4, 28, 28,
                    outline=color,
                    width=2
                )
            
            # 步骤名称
            text_color = self._colors['text'] if is_active else self._colors['text_inactive']
            
            if _CTK_AVAILABLE:
                label = ctk.CTkLabel(
                    step_frame,
                    text=step_name,
                    text_color=text_color,
                    font=("Arial", 12)
                )
            else:
                label = tk.Label(
                    step_frame,
                    text=step_name,
                    fg=text_color,
                    font=("Arial", 12)
                )
            
            label.pack(pady=(5, 0))
            
            self._step_widgets.append((indicator, label))
    
    def set_step(self, step: int):
        """设置当前步骤
        
        Args:
            step: 步骤索引 (0开始)
        """
        if 0 <= step < len(self._steps):
            self._current_step = step
            # 实际项目中应重新绘制步骤指示器
    
    def next_step(self):
        """前进到下一步"""
        if self._current_step < len(self._steps) - 1:
            self.set_step(self._current_step + 1)
    
    def prev_step(self):
        """返回上一步"""
        if self._current_step > 0:
            self.set_step(self._current_step - 1)
    
    def pack(self, **kwargs):
        """打包"""
        self._container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self._container.grid(**kwargs)


# 便捷函数
def create_linear_progress(
    master,
    width: int = 300,
    indeterminate: bool = False,
    theme: str = "dark"
) -> LinearProgress:
    """快速创建线性进度条
    
    Args:
        master: 父容器
        width: 宽度
        indeterminate: 是否不确定状态
        theme: 主题
        
    Returns:
        LinearProgress实例
    """
    return LinearProgress(
        master,
        width=width,
        indeterminate=indeterminate,
        theme=theme
    )


def create_circular_progress(
    master,
    size: int = 100,
    indeterminate: bool = False,
    theme: str = "dark"
) -> CircularProgress:
    """快速创建圆形进度条
    
    Args:
        master: 父容器
        size: 尺寸
        indeterminate: 是否不确定状态
        theme: 主题
        
    Returns:
        CircularProgress实例
    """
    return CircularProgress(
        master,
        size=size,
        indeterminate=indeterminate,
        theme=theme
    )
