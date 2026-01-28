"""
微交互动画库 (Micro Interactions)
符合2026年设计趋势的精致交互动画

功能特性:
- 点击反馈(scale/ripple)
- 悬停效果(translateY/阴影变化)
- 加载动画(Skeleton/Spinner/Pulse)
- 过渡动画(展开收起/列表增删)
- 焦点指示器

安全措施:
- 动画不阻塞主线程
- 资源自动释放
- 防止动画堆积
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Dict, List, Literal, Tuple
from dataclasses import dataclass
import time
import math
import logging

logger = logging.getLogger(__name__)


class RippleEffect:
    """水波纹点击效果"""
    
    def __init__(
        self,
        widget: tk.Widget,
        color: str = "#ffffff",
        duration: int = 400,
        max_radius: int = 100
    ):
        self.widget = widget
        self.color = color
        self.duration = duration
        self.max_radius = max_radius
        
        self._canvas: Optional[tk.Canvas] = None
        self._ripple_id: Optional[int] = None
        self._animation_id: Optional[str] = None
        self._is_animating = False
        
        # 绑定点击事件
        self.widget.bind("<Button-1>", self._on_click, add="+")
    
    def _on_click(self, event):
        """点击触发水波纹"""
        if self._is_animating:
            return
        
        self._is_animating = True
        
        # 创建Canvas覆盖层
        widget_width = self.widget.winfo_width()
        widget_height = self.widget.winfo_height()
        
        self._canvas = tk.Canvas(
            self.widget,
            width=widget_width,
            height=widget_height,
            highlightthickness=0,
            bg=""
        )
        self._canvas.place(x=0, y=0)
        
        # 点击位置
        click_x = event.x
        click_y = event.y
        
        # 计算最大半径
        corners = [
            (0, 0), (widget_width, 0),
            (0, widget_height), (widget_width, widget_height)
        ]
        max_dist = max(
            math.sqrt((click_x - cx) ** 2 + (click_y - cy) ** 2)
            for cx, cy in corners
        )
        self.max_radius = int(max_dist)
        
        # 创建初始圆形
        self._ripple_id = self._canvas.create_oval(
            click_x, click_y, click_x, click_y,
            fill=self.color,
            outline=""
        )
        
        # 动画
        self._animate_ripple(click_x, click_y, 0)
    
    def _animate_ripple(self, cx: int, cy: int, step: int):
        """执行水波纹动画"""
        total_steps = self.duration // 16
        
        if step > total_steps:
            self._cleanup()
            return
        
        progress = step / total_steps
        radius = int(self.max_radius * self._ease_out(progress))
        
        # 计算透明度（模拟淡出）
        alpha = int(80 * (1 - progress))
        
        # 更新圆形
        self._canvas.coords(
            self._ripple_id,
            cx - radius, cy - radius,
            cx + radius, cy + radius
        )
        
        # Tkinter不支持真正透明度，用颜色模拟
        try:
            gray_val = min(255, 200 + int(55 * progress))
            self._canvas.itemconfig(
                self._ripple_id,
                fill=f"#{gray_val:02x}{gray_val:02x}{gray_val:02x}"
            )
        except tk.TclError:
            pass
        
        self._animation_id = self.widget.after(
            16,
            lambda: self._animate_ripple(cx, cy, step + 1)
        )
    
    def _ease_out(self, t: float) -> float:
        return 1 - (1 - t) ** 3
    
    def _cleanup(self):
        """清理"""
        self._is_animating = False
        if self._canvas:
            self._canvas.destroy()
            self._canvas = None
        self._ripple_id = None
    
    def destroy(self):
        """销毁"""
        if self._animation_id:
            self.widget.after_cancel(self._animation_id)
        self._cleanup()
        try:
            self.widget.unbind("<Button-1>")
        except tk.TclError:
            pass


class ScaleEffect:
    """点击缩放效果"""
    
    def __init__(
        self,
        widget: tk.Widget,
        scale_down: float = 0.95,
        duration: int = 100
    ):
        self.widget = widget
        self.scale_down = scale_down
        self.duration = duration
        
        self._original_width = 0
        self._original_height = 0
        self._is_animating = False
        
        # 绑定事件
        self.widget.bind("<ButtonPress-1>", self._on_press, add="+")
        self.widget.bind("<ButtonRelease-1>", self._on_release, add="+")
    
    def _on_press(self, event):
        """按下缩小"""
        if self._is_animating:
            return
        
        self._original_width = self.widget.winfo_width()
        self._original_height = self.widget.winfo_height()
        
        self._animate_scale(1.0, self.scale_down)
    
    def _on_release(self, event):
        """释放恢复"""
        self._animate_scale(self.scale_down, 1.0)
    
    def _animate_scale(self, from_scale: float, to_scale: float):
        """执行缩放动画"""
        self._is_animating = True
        steps = self.duration // 16
        
        def animate(step):
            if step > steps:
                self._is_animating = False
                return
            
            progress = step / steps
            current_scale = from_scale + (to_scale - from_scale) * self._ease_out(progress)
            
            # 通过padding模拟缩放
            padding = int((1 - current_scale) * 5)
            try:
                self.widget.configure(padx=padding, pady=padding)
            except tk.TclError:
                pass
            
            self.widget.after(16, lambda: animate(step + 1))
        
        animate(1)
    
    def _ease_out(self, t: float) -> float:
        return 1 - (1 - t) ** 2
    
    def destroy(self):
        try:
            self.widget.unbind("<ButtonPress-1>")
            self.widget.unbind("<ButtonRelease-1>")
        except tk.TclError:
            pass


class HoverEffect:
    """悬停效果"""
    
    def __init__(
        self,
        widget: tk.Widget,
        hover_bg: Optional[str] = None,
        normal_bg: Optional[str] = None,
        lift_pixels: int = 2,
        duration: int = 150
    ):
        self.widget = widget
        self.hover_bg = hover_bg
        self.normal_bg = normal_bg or widget.cget("bg")
        self.lift_pixels = lift_pixels
        self.duration = duration
        
        self._original_y = 0
        self._is_hovered = False
        
        # 绑定事件
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        """鼠标进入"""
        if self._is_hovered:
            return
        
        self._is_hovered = True
        
        # 背景变化
        if self.hover_bg:
            try:
                self.widget.configure(bg=self.hover_bg)
                for child in self.widget.winfo_children():
                    try:
                        child.configure(bg=self.hover_bg)
                    except tk.TclError:
                        pass
            except tk.TclError:
                pass
        
        # 上浮效果（通过place微调）
        if self.lift_pixels > 0:
            try:
                info = self.widget.place_info()
                if info:
                    current_y = int(info.get("y", 0))
                    self._original_y = current_y
                    self.widget.place(y=current_y - self.lift_pixels)
            except (tk.TclError, ValueError):
                pass
    
    def _on_leave(self, event):
        """鼠标离开"""
        if not self._is_hovered:
            return
        
        self._is_hovered = False
        
        # 恢复背景
        try:
            self.widget.configure(bg=self.normal_bg)
            for child in self.widget.winfo_children():
                try:
                    child.configure(bg=self.normal_bg)
                except tk.TclError:
                    pass
        except tk.TclError:
            pass
        
        # 恢复位置
        if self.lift_pixels > 0:
            try:
                self.widget.place(y=self._original_y)
            except tk.TclError:
                pass
    
    def destroy(self):
        try:
            self.widget.unbind("<Enter>")
            self.widget.unbind("<Leave>")
        except tk.TclError:
            pass


class SkeletonLoader(tk.Frame):
    """骨架屏加载动画"""
    
    def __init__(
        self,
        parent: tk.Widget,
        width: int = 200,
        height: int = 20,
        bg_color: str = "#2a2a2a",
        highlight_color: str = "#3a3a3a",
        **kwargs
    ):
        super().__init__(parent, width=width, height=height, **kwargs)
        
        self.bg_color = bg_color
        self.highlight_color = highlight_color
        self._width = width
        self._height = height
        
        self.configure(bg=bg_color)
        self.pack_propagate(False)
        
        # Canvas绘制
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 高亮条
        self._highlight = self.canvas.create_rectangle(
            -50, 0, 0, height,
            fill=highlight_color,
            outline=""
        )
        
        self._is_animating = True
        self._animation_id = None
        self._animate()
    
    def _animate(self):
        """执行动画"""
        if not self._is_animating:
            return
        
        # 移动高亮条
        self.canvas.move(self._highlight, 5, 0)
        
        # 获取当前位置
        coords = self.canvas.coords(self._highlight)
        if coords[0] > self._width:
            self.canvas.coords(self._highlight, -50, 0, 0, self._height)
        
        self._animation_id = self.after(30, self._animate)
    
    def stop(self):
        """停止动画"""
        self._is_animating = False
        if self._animation_id:
            self.after_cancel(self._animation_id)
    
    def destroy(self):
        self.stop()
        super().destroy()


class Spinner(tk.Canvas):
    """旋转加载指示器"""
    
    def __init__(
        self,
        parent: tk.Widget,
        size: int = 32,
        color: str = "#3b82f6",
        thickness: int = 3,
        **kwargs
    ):
        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            **kwargs
        )
        
        self.size = size
        self.color = color
        self.thickness = thickness
        
        self._angle = 0
        self._arc_length = 90
        self._is_animating = True
        self._animation_id = None
        
        self._draw()
        self._animate()
    
    def _draw(self):
        """绘制圆弧"""
        self.delete("arc")
        
        padding = self.thickness + 2
        self.create_arc(
            padding, padding,
            self.size - padding, self.size - padding,
            start=self._angle,
            extent=self._arc_length,
            style=tk.ARC,
            outline=self.color,
            width=self.thickness,
            tags="arc"
        )
    
    def _animate(self):
        """执行旋转动画"""
        if not self._is_animating:
            return
        
        self._angle = (self._angle + 10) % 360
        self._draw()
        
        self._animation_id = self.after(30, self._animate)
    
    def stop(self):
        """停止动画"""
        self._is_animating = False
        if self._animation_id:
            self.after_cancel(self._animation_id)
    
    def start(self):
        """启动动画"""
        if not self._is_animating:
            self._is_animating = True
            self._animate()
    
    def destroy(self):
        self.stop()
        super().destroy()


class PulseEffect:
    """脉冲效果（元素闪烁）"""
    
    def __init__(
        self,
        widget: tk.Widget,
        color1: str = "#3b82f6",
        color2: str = "#60a5fa",
        duration: int = 1000
    ):
        self.widget = widget
        self.color1 = color1
        self.color2 = color2
        self.duration = duration
        
        self._is_animating = False
        self._animation_id = None
        self._step = 0
    
    def start(self):
        """开始脉冲"""
        if self._is_animating:
            return
        
        self._is_animating = True
        self._animate()
    
    def stop(self):
        """停止脉冲"""
        self._is_animating = False
        if self._animation_id:
            self.widget.after_cancel(self._animation_id)
    
    def _animate(self):
        """执行脉冲动画"""
        if not self._is_animating:
            return
        
        # 计算颜色插值
        progress = (math.sin(self._step * 0.1) + 1) / 2
        
        r1, g1, b1 = self._hex_to_rgb(self.color1)
        r2, g2, b2 = self._hex_to_rgb(self.color2)
        
        r = int(r1 + (r2 - r1) * progress)
        g = int(g1 + (g2 - g1) * progress)
        b = int(b1 + (b2 - b1) * progress)
        
        try:
            self.widget.configure(bg=f"#{r:02x}{g:02x}{b:02x}")
        except tk.TclError:
            pass
        
        self._step += 1
        self._animation_id = self.widget.after(50, self._animate)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def destroy(self):
        self.stop()


class CollapseExpand:
    """展开/收起动画"""
    
    def __init__(
        self,
        widget: tk.Widget,
        expanded_height: int,
        collapsed_height: int = 0,
        duration: int = 300
    ):
        self.widget = widget
        self.expanded_height = expanded_height
        self.collapsed_height = collapsed_height
        self.duration = duration
        
        self._is_expanded = True
        self._is_animating = False
    
    def toggle(self, on_complete: Optional[Callable[[], None]] = None):
        """切换状态"""
        if self._is_animating:
            return
        
        if self._is_expanded:
            self.collapse(on_complete)
        else:
            self.expand(on_complete)
    
    def expand(self, on_complete: Optional[Callable[[], None]] = None):
        """展开"""
        if self._is_expanded or self._is_animating:
            return
        
        self._animate(
            self.collapsed_height,
            self.expanded_height,
            lambda: self._on_expand_complete(on_complete)
        )
    
    def collapse(self, on_complete: Optional[Callable[[], None]] = None):
        """收起"""
        if not self._is_expanded or self._is_animating:
            return
        
        self._animate(
            self.expanded_height,
            self.collapsed_height,
            lambda: self._on_collapse_complete(on_complete)
        )
    
    def _animate(
        self,
        from_height: int,
        to_height: int,
        on_complete: Callable[[], None]
    ):
        """执行动画"""
        self._is_animating = True
        steps = self.duration // 16
        
        def animate(step):
            if step > steps:
                self._is_animating = False
                on_complete()
                return
            
            progress = self._ease_out(step / steps)
            current_height = int(from_height + (to_height - from_height) * progress)
            
            try:
                self.widget.configure(height=max(1, current_height))
            except tk.TclError:
                pass
            
            self.widget.after(16, lambda: animate(step + 1))
        
        animate(1)
    
    def _on_expand_complete(self, callback):
        self._is_expanded = True
        if callback:
            callback()
    
    def _on_collapse_complete(self, callback):
        self._is_expanded = False
        if callback:
            callback()
    
    def _ease_out(self, t: float) -> float:
        return 1 - (1 - t) ** 3
    
    def is_expanded(self) -> bool:
        return self._is_expanded


class FocusRing:
    """焦点指示环"""
    
    def __init__(
        self,
        widget: tk.Widget,
        color: str = "#3b82f6",
        width: int = 2
    ):
        self.widget = widget
        self.color = color
        self.width = width
        
        self._ring_frame: Optional[tk.Frame] = None
        
        # 绑定焦点事件
        self.widget.bind("<FocusIn>", self._on_focus_in)
        self.widget.bind("<FocusOut>", self._on_focus_out)
    
    def _on_focus_in(self, event):
        """获得焦点"""
        if self._ring_frame:
            return
        
        # 创建边框框架
        parent = self.widget.master
        
        self._ring_frame = tk.Frame(
            parent,
            bg=self.color,
            bd=0
        )
        
        # 定位在widget周围
        self.widget.update_idletasks()
        x = self.widget.winfo_x() - self.width
        y = self.widget.winfo_y() - self.width
        w = self.widget.winfo_width() + 2 * self.width
        h = self.widget.winfo_height() + 2 * self.width
        
        self._ring_frame.place(x=x, y=y, width=w, height=h)
        self._ring_frame.lower(self.widget)
    
    def _on_focus_out(self, event):
        """失去焦点"""
        if self._ring_frame:
            self._ring_frame.destroy()
            self._ring_frame = None
    
    def destroy(self):
        try:
            self.widget.unbind("<FocusIn>")
            self.widget.unbind("<FocusOut>")
        except tk.TclError:
            pass
        
        if self._ring_frame:
            self._ring_frame.destroy()


class MicroInteractions:
    """微交互管理器"""
    
    _effects: Dict[int, List] = {}
    
    @classmethod
    def add_ripple(
        cls,
        widget: tk.Widget,
        color: str = "#ffffff",
        duration: int = 400
    ) -> RippleEffect:
        """添加水波纹效果"""
        effect = RippleEffect(widget, color, duration)
        cls._register(widget, effect)
        return effect
    
    @classmethod
    def add_scale(
        cls,
        widget: tk.Widget,
        scale_down: float = 0.95,
        duration: int = 100
    ) -> ScaleEffect:
        """添加缩放效果"""
        effect = ScaleEffect(widget, scale_down, duration)
        cls._register(widget, effect)
        return effect
    
    @classmethod
    def add_hover(
        cls,
        widget: tk.Widget,
        hover_bg: Optional[str] = None,
        normal_bg: Optional[str] = None,
        lift_pixels: int = 2
    ) -> HoverEffect:
        """添加悬停效果"""
        effect = HoverEffect(widget, hover_bg, normal_bg, lift_pixels)
        cls._register(widget, effect)
        return effect
    
    @classmethod
    def add_pulse(
        cls,
        widget: tk.Widget,
        color1: str = "#3b82f6",
        color2: str = "#60a5fa"
    ) -> PulseEffect:
        """添加脉冲效果"""
        effect = PulseEffect(widget, color1, color2)
        cls._register(widget, effect)
        return effect
    
    @classmethod
    def add_focus_ring(
        cls,
        widget: tk.Widget,
        color: str = "#3b82f6",
        width: int = 2
    ) -> FocusRing:
        """添加焦点环"""
        effect = FocusRing(widget, color, width)
        cls._register(widget, effect)
        return effect
    
    @classmethod
    def _register(cls, widget: tk.Widget, effect):
        """注册效果"""
        widget_id = id(widget)
        if widget_id not in cls._effects:
            cls._effects[widget_id] = []
        cls._effects[widget_id].append(effect)
    
    @classmethod
    def remove_all(cls, widget: tk.Widget):
        """移除widget的所有效果"""
        widget_id = id(widget)
        if widget_id in cls._effects:
            for effect in cls._effects[widget_id]:
                if hasattr(effect, "destroy"):
                    effect.destroy()
            del cls._effects[widget_id]
    
    @classmethod
    def cleanup(cls):
        """清理所有效果"""
        for widget_id, effects in list(cls._effects.items()):
            for effect in effects:
                if hasattr(effect, "destroy"):
                    effect.destroy()
        cls._effects.clear()


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("微交互动画测试")
    root.geometry("800x600")
    root.configure(bg="#121212")
    
    # 标题
    tk.Label(
        root,
        text="微交互动画演示",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=20)
    
    # 水波纹按钮
    ripple_btn = tk.Label(
        root,
        text="点击查看水波纹效果",
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        padx=20,
        pady=12,
        cursor="hand2"
    )
    ripple_btn.pack(pady=10)
    MicroInteractions.add_ripple(ripple_btn)
    
    # 缩放按钮
    scale_btn = tk.Label(
        root,
        text="点击查看缩放效果",
        bg="#10b981",
        fg="#ffffff",
        font=("Segoe UI", 12),
        padx=20,
        pady=12,
        cursor="hand2"
    )
    scale_btn.pack(pady=10)
    MicroInteractions.add_scale(scale_btn)
    
    # 悬停效果
    hover_frame = tk.Frame(root, bg="#2a2a2a", padx=20, pady=12)
    hover_frame.pack(pady=10)
    tk.Label(
        hover_frame,
        text="悬停查看上浮效果",
        bg="#2a2a2a",
        fg="#e5e5e5",
        font=("Segoe UI", 12)
    ).pack()
    MicroInteractions.add_hover(hover_frame, hover_bg="#3a3a3a", normal_bg="#2a2a2a")
    
    # Skeleton加载
    tk.Label(
        root,
        text="Skeleton 骨架屏:",
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10)
    ).pack(pady=(20, 5))
    
    skeleton = SkeletonLoader(root, width=300, height=20, bg_color="#2a2a2a")
    skeleton.pack(pady=5)
    
    # Spinner
    tk.Label(
        root,
        text="Spinner 加载指示器:",
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10)
    ).pack(pady=(20, 5))
    
    spinner = Spinner(root, size=40, color="#3b82f6", bg="#121212")
    spinner.pack(pady=5)
    
    # 脉冲效果
    pulse_label = tk.Label(
        root,
        text="  脉冲效果  ",
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        padx=20,
        pady=10
    )
    pulse_label.pack(pady=20)
    pulse = MicroInteractions.add_pulse(pulse_label, "#3b82f6", "#60a5fa")
    pulse.start()
    
    root.mainloop()
