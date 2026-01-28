"""
响应式布局系统 (Responsive Layout System)
符合2026年设计趋势的自适应布局实现

功能特性:
- 断点系统(XS/SM/MD/LG/XL)
- 窗口大小变化监听
- 自动布局调整
- 响应式网格系统
- 抽屉式侧边栏(小屏幕)

安全措施:
- 窗口调整事件节流(防止性能问题)
- 回调数量限制
- 异常处理
"""

import tkinter as tk
from typing import Dict, List, Callable, Optional, Literal, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import time

logger = logging.getLogger(__name__)


class Breakpoint(Enum):
    """断点枚举"""
    XS = "xs"   # < 768px (手机)
    SM = "sm"   # 768-1024px (平板竖屏)
    MD = "md"   # 1024-1440px (平板横屏/小笔记本)
    LG = "lg"   # 1440-1920px (桌面)
    XL = "xl"   # > 1920px (大屏幕)


@dataclass
class BreakpointConfig:
    """断点配置"""
    xs_max: int = 768
    sm_max: int = 1024
    md_max: int = 1440
    lg_max: int = 1920


class BreakpointManager:
    """断点管理器 - 监听窗口大小变化"""
    
    # 安全限制
    MAX_CALLBACKS = 50
    THROTTLE_MS = 100
    
    def __init__(
        self,
        root: tk.Tk,
        config: Optional[BreakpointConfig] = None
    ):
        self.root = root
        self.config = config or BreakpointConfig()
        
        self._callbacks: List[Callable[[Breakpoint, int, int], None]] = []
        self._current_breakpoint: Optional[Breakpoint] = None
        self._last_resize_time: float = 0
        self._pending_resize: Optional[str] = None
        
        # 绑定窗口大小变化事件
        self.root.bind("<Configure>", self._on_configure)
        
        # 初始化当前断点
        self._update_breakpoint()
    
    def _on_configure(self, event):
        """窗口配置变化事件（节流处理）"""
        # 只处理根窗口的事件
        if event.widget != self.root:
            return
        
        current_time = time.time() * 1000
        
        # 节流：如果距离上次处理不足阈值，则延迟处理
        if current_time - self._last_resize_time < self.THROTTLE_MS:
            # 取消之前的延迟任务
            if self._pending_resize:
                self.root.after_cancel(self._pending_resize)
            
            # 设置新的延迟任务
            self._pending_resize = self.root.after(
                self.THROTTLE_MS,
                self._update_breakpoint
            )
            return
        
        self._last_resize_time = current_time
        self._update_breakpoint()
    
    def _update_breakpoint(self):
        """更新当前断点"""
        self._pending_resize = None
        
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        
        # 确定当前断点
        new_breakpoint = self._get_breakpoint(width)
        
        # 如果断点变化，触发回调
        if new_breakpoint != self._current_breakpoint:
            old_breakpoint = self._current_breakpoint
            self._current_breakpoint = new_breakpoint
            
            logger.info(f"断点变化: {old_breakpoint} -> {new_breakpoint} (width={width})")
            
            for callback in self._callbacks:
                try:
                    callback(new_breakpoint, width, height)
                except Exception as e:
                    logger.error(f"断点回调执行失败: {e}")
    
    def _get_breakpoint(self, width: int) -> Breakpoint:
        """根据宽度获取断点"""
        if width < self.config.xs_max:
            return Breakpoint.XS
        elif width < self.config.sm_max:
            return Breakpoint.SM
        elif width < self.config.md_max:
            return Breakpoint.MD
        elif width < self.config.lg_max:
            return Breakpoint.LG
        else:
            return Breakpoint.XL
    
    def on_breakpoint_change(
        self,
        callback: Callable[[Breakpoint, int, int], None]
    ) -> bool:
        """注册断点变化回调"""
        if len(self._callbacks) >= self.MAX_CALLBACKS:
            logger.warning(f"回调数量已达上限({self.MAX_CALLBACKS})")
            return False
        
        self._callbacks.append(callback)
        return True
    
    def off_breakpoint_change(
        self,
        callback: Callable[[Breakpoint, int, int], None]
    ):
        """移除断点变化回调"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_current_breakpoint(self) -> Breakpoint:
        """获取当前断点"""
        if self._current_breakpoint is None:
            self._update_breakpoint()
        return self._current_breakpoint
    
    def get_window_size(self) -> Tuple[int, int]:
        """获取当前窗口大小"""
        return self.root.winfo_width(), self.root.winfo_height()
    
    def is_mobile(self) -> bool:
        """是否为移动端尺寸"""
        return self.get_current_breakpoint() == Breakpoint.XS
    
    def is_tablet(self) -> bool:
        """是否为平板尺寸"""
        bp = self.get_current_breakpoint()
        return bp in (Breakpoint.SM, Breakpoint.MD)
    
    def is_desktop(self) -> bool:
        """是否为桌面尺寸"""
        bp = self.get_current_breakpoint()
        return bp in (Breakpoint.LG, Breakpoint.XL)
    
    def destroy(self):
        """清理资源"""
        self.root.unbind("<Configure>")
        if self._pending_resize:
            self.root.after_cancel(self._pending_resize)
        self._callbacks.clear()


class ResponsiveGrid(tk.Frame):
    """响应式网格容器"""
    
    def __init__(
        self,
        parent: tk.Widget,
        breakpoint_manager: BreakpointManager,
        columns: Dict[Breakpoint, int] = None,
        gap: int = 16,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.bp_manager = breakpoint_manager
        self.gap = gap
        
        # 各断点列数配置
        self.columns = columns or {
            Breakpoint.XS: 1,
            Breakpoint.SM: 2,
            Breakpoint.MD: 3,
            Breakpoint.LG: 4,
            Breakpoint.XL: 5
        }
        
        self._items: List[tk.Widget] = []
        
        # 监听断点变化
        self.bp_manager.on_breakpoint_change(self._on_breakpoint_change)
        
        # 初始布局
        self.after(100, self._relayout)
    
    def _on_breakpoint_change(self, bp: Breakpoint, width: int, height: int):
        """断点变化时重新布局"""
        self._relayout()
    
    def _relayout(self):
        """重新计算布局"""
        if not self._items:
            return
        
        bp = self.bp_manager.get_current_breakpoint()
        cols = self.columns.get(bp, 3)
        
        # 计算每列宽度
        container_width = self.winfo_width()
        if container_width <= 1:
            container_width = 800  # 默认宽度
        
        item_width = (container_width - (cols + 1) * self.gap) // cols
        
        # 重新放置所有项
        for i, item in enumerate(self._items):
            row = i // cols
            col = i % cols
            
            x = self.gap + col * (item_width + self.gap)
            y = self.gap + row * (item_width + self.gap)
            
            item.place(x=x, y=y, width=item_width, height=item_width)
    
    def add_item(self, item: tk.Widget):
        """添加网格项"""
        self._items.append(item)
        self._relayout()
    
    def remove_item(self, item: tk.Widget):
        """移除网格项"""
        if item in self._items:
            self._items.remove(item)
            item.place_forget()
            self._relayout()
    
    def clear(self):
        """清空所有项"""
        for item in self._items:
            item.destroy()
        self._items.clear()
    
    def destroy(self):
        """清理资源"""
        self.bp_manager.off_breakpoint_change(self._on_breakpoint_change)
        self.clear()
        super().destroy()


class ResponsiveValue:
    """响应式值 - 根据断点返回不同值"""
    
    def __init__(
        self,
        breakpoint_manager: BreakpointManager,
        values: Dict[Breakpoint, any],
        default: any = None
    ):
        self.bp_manager = breakpoint_manager
        self.values = values
        self.default = default
    
    def get(self) -> any:
        """获取当前断点对应的值"""
        bp = self.bp_manager.get_current_breakpoint()
        return self.values.get(bp, self.default)
    
    def __call__(self) -> any:
        return self.get()


class DrawerSidebar(tk.Frame):
    """抽屉式侧边栏（移动端）"""
    
    def __init__(
        self,
        parent: tk.Widget,
        width: int = 280,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.drawer_width = width
        self._is_open = False
        self._animating = False
        
        # 样式
        self.colors = {
            "bg": "#1a1a1a",
            "overlay": "#000000"
        }
        
        self.configure(bg=self.colors["bg"])
        
        # 创建遮罩层
        self.overlay = tk.Frame(parent, bg=self.colors["overlay"])
        self.overlay.bind("<Button-1>", lambda e: self.close())
        
        # 初始隐藏
        self.place_forget()
        self.overlay.place_forget()
    
    def open(self):
        """打开抽屉"""
        if self._is_open or self._animating:
            return
        
        self._is_open = True
        self._animating = True
        
        # 显示遮罩
        self.overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.overlay.lift()
        
        # 动画打开
        self._animate_open()
    
    def close(self):
        """关闭抽屉"""
        if not self._is_open or self._animating:
            return
        
        self._animating = True
        
        # 动画关闭
        self._animate_close()
    
    def _animate_open(self):
        """打开动画"""
        self.place(x=-self.drawer_width, y=0, width=self.drawer_width, relheight=1.0)
        self.lift()
        
        steps = 15
        step_delay = 20
        
        def animate_step(current_step):
            if current_step > steps:
                self._animating = False
                return
            
            progress = self._ease_out(current_step / steps)
            x = int(-self.drawer_width * (1 - progress))
            
            self.place(x=x)
            
            # 遮罩透明度（模拟）
            overlay_alpha = int(128 * progress)
            self.overlay.configure(bg=f"#{overlay_alpha:02x}{overlay_alpha:02x}{overlay_alpha:02x}")
            
            self.after(step_delay, lambda: animate_step(current_step + 1))
        
        animate_step(1)
    
    def _animate_close(self):
        """关闭动画"""
        steps = 15
        step_delay = 20
        
        def animate_step(current_step):
            if current_step > steps:
                self._animating = False
                self._is_open = False
                self.place_forget()
                self.overlay.place_forget()
                return
            
            progress = self._ease_out(current_step / steps)
            x = int(-self.drawer_width * progress)
            
            self.place(x=x)
            
            self.after(step_delay, lambda: animate_step(current_step + 1))
        
        animate_step(1)
    
    def _ease_out(self, t: float) -> float:
        """ease-out缓动函数"""
        return 1 - (1 - t) ** 3
    
    def toggle(self):
        """切换状态"""
        if self._is_open:
            self.close()
        else:
            self.open()
    
    def is_open(self) -> bool:
        """是否打开状态"""
        return self._is_open


class ResponsiveLayout:
    """响应式布局助手"""
    
    def __init__(self, breakpoint_manager: BreakpointManager):
        self.bp_manager = breakpoint_manager
    
    def apply_responsive_styles(
        self,
        widget: tk.Widget,
        styles: Dict[Breakpoint, Dict[str, any]]
    ):
        """应用响应式样式"""
        def on_change(bp: Breakpoint, w: int, h: int):
            if bp in styles:
                for key, value in styles[bp].items():
                    try:
                        widget.configure(**{key: value})
                    except tk.TclError:
                        pass
        
        self.bp_manager.on_breakpoint_change(on_change)
        
        # 立即应用当前断点样式
        current_bp = self.bp_manager.get_current_breakpoint()
        if current_bp in styles:
            for key, value in styles[current_bp].items():
                try:
                    widget.configure(**{key: value})
                except tk.TclError:
                    pass
    
    def responsive_padding(
        self,
        xs: int = 8,
        sm: int = 12,
        md: int = 16,
        lg: int = 20,
        xl: int = 24
    ) -> int:
        """获取响应式padding值"""
        bp = self.bp_manager.get_current_breakpoint()
        mapping = {
            Breakpoint.XS: xs,
            Breakpoint.SM: sm,
            Breakpoint.MD: md,
            Breakpoint.LG: lg,
            Breakpoint.XL: xl
        }
        return mapping.get(bp, md)
    
    def responsive_font_size(
        self,
        xs: int = 12,
        sm: int = 13,
        md: int = 14,
        lg: int = 15,
        xl: int = 16
    ) -> int:
        """获取响应式字体大小"""
        bp = self.bp_manager.get_current_breakpoint()
        mapping = {
            Breakpoint.XS: xs,
            Breakpoint.SM: sm,
            Breakpoint.MD: md,
            Breakpoint.LG: lg,
            Breakpoint.XL: xl
        }
        return mapping.get(bp, md)


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("响应式布局测试")
    root.geometry("1200x800")
    root.configure(bg="#121212")
    
    # 创建断点管理器
    bp_manager = BreakpointManager(root)
    
    # 断点变化回调
    def on_bp_change(bp: Breakpoint, width: int, height: int):
        info_label.config(text=f"断点: {bp.value} | 宽度: {width}px | 高度: {height}px")
    
    bp_manager.on_breakpoint_change(on_bp_change)
    
    # 信息标签
    info_label = tk.Label(
        root,
        text="调整窗口大小查看断点变化",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 14)
    )
    info_label.pack(pady=20)
    
    # 响应式网格
    grid = ResponsiveGrid(
        root,
        bp_manager,
        gap=20,
        bg="#121212"
    )
    grid.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 添加测试卡片
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"]
    for i in range(12):
        card = tk.Frame(grid, bg=colors[i % len(colors)])
        tk.Label(
            card,
            text=f"Card {i+1}",
            bg=colors[i % len(colors)],
            fg="#ffffff",
            font=("Segoe UI", 12, "bold")
        ).pack(expand=True)
        grid.add_item(card)
    
    root.mainloop()
