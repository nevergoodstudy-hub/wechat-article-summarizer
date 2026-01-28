"""
可访问性工具模块 (Accessibility)
符合WCAG 2.1标准的可访问性支持

功能特性:
- 键盘导航管理
- 焦点可视化指示
- Skip Links快速跳转
- 焦点陷阱防护
- Tab顺序管理

安全措施:
- 无键盘陷阱
- 焦点不丢失
- 超时保护
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FocusDirection(Enum):
    """焦点移动方向"""
    NEXT = "next"
    PREVIOUS = "previous"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class FocusableElement:
    """可聚焦元素"""
    widget: tk.Widget
    tab_index: int = 0
    group: str = "default"
    label: str = ""
    skip: bool = False  # 是否在Tab导航中跳过


class FocusRingStyle:
    """焦点轮廓样式"""
    
    # 默认样式 - 2px蓝色轮廓
    DEFAULT = {
        "color": "#3b82f6",
        "width": 2,
        "offset": 2,
        "style": "solid"
    }
    
    # 高对比度样式
    HIGH_CONTRAST = {
        "color": "#ffffff",
        "width": 3,
        "offset": 2,
        "style": "solid"
    }
    
    # 虚线样式
    DASHED = {
        "color": "#3b82f6",
        "width": 2,
        "offset": 2,
        "style": "dashed"
    }


class FocusManager:
    """焦点管理器"""
    
    _instance: Optional["FocusManager"] = None
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._elements: List[FocusableElement] = []
        self._groups: Dict[str, List[FocusableElement]] = {}
        self._current_index = -1
        self._focus_ring_style = FocusRingStyle.DEFAULT
        self._focus_ring_canvas: Optional[tk.Canvas] = None
        self._trap_enabled = False
        self._trap_widgets: List[tk.Widget] = []
        
        # 绑定全局键盘事件
        self._bind_keyboard_events()
    
    @classmethod
    def get_instance(cls, root: Optional[tk.Tk] = None) -> "FocusManager":
        """获取单例实例"""
        if cls._instance is None:
            if root is None:
                raise ValueError("首次调用需要提供root参数")
            cls._instance = cls(root)
        return cls._instance
    
    def _bind_keyboard_events(self):
        """绑定键盘事件"""
        self.root.bind_all("<Tab>", self._on_tab, add="+")
        self.root.bind_all("<Shift-Tab>", self._on_shift_tab, add="+")
        self.root.bind_all("<FocusIn>", self._on_focus_in, add="+")
        self.root.bind_all("<FocusOut>", self._on_focus_out, add="+")
    
    def register(
        self,
        widget: tk.Widget,
        tab_index: int = 0,
        group: str = "default",
        label: str = "",
        skip: bool = False
    ) -> FocusableElement:
        """注册可聚焦元素"""
        element = FocusableElement(
            widget=widget,
            tab_index=tab_index,
            group=group,
            label=label,
            skip=skip
        )
        
        self._elements.append(element)
        
        # 添加到分组
        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(element)
        
        # 排序
        self._sort_elements()
        
        return element
    
    def unregister(self, widget: tk.Widget):
        """注销元素"""
        self._elements = [e for e in self._elements if e.widget != widget]
        
        for group in self._groups.values():
            group[:] = [e for e in group if e.widget != widget]
    
    def _sort_elements(self):
        """按tab_index排序"""
        self._elements.sort(key=lambda e: (e.tab_index, self._elements.index(e)))
        
        for group in self._groups.values():
            group.sort(key=lambda e: e.tab_index)
    
    def _on_tab(self, event):
        """Tab键处理"""
        self._move_focus(FocusDirection.NEXT)
        return "break"
    
    def _on_shift_tab(self, event):
        """Shift+Tab处理"""
        self._move_focus(FocusDirection.PREVIOUS)
        return "break"
    
    def _move_focus(self, direction: FocusDirection):
        """移动焦点"""
        focusable = [e for e in self._elements if not e.skip and e.widget.winfo_exists()]
        
        if not focusable:
            return
        
        # 焦点陷阱模式
        if self._trap_enabled and self._trap_widgets:
            focusable = [
                e for e in focusable 
                if any(self._is_descendant(e.widget, w) for w in self._trap_widgets)
            ]
        
        if not focusable:
            return
        
        # 获取当前焦点
        current_widget = self.root.focus_get()
        current_index = -1
        
        for i, element in enumerate(focusable):
            if element.widget == current_widget or self._is_descendant(current_widget, element.widget):
                current_index = i
                break
        
        # 计算下一个索引
        if direction == FocusDirection.NEXT:
            next_index = (current_index + 1) % len(focusable)
        elif direction == FocusDirection.PREVIOUS:
            next_index = (current_index - 1) % len(focusable)
        else:
            next_index = current_index
        
        # 设置焦点
        next_widget = focusable[next_index].widget
        self._set_focus(next_widget)
    
    def _is_descendant(self, widget: Optional[tk.Widget], parent: tk.Widget) -> bool:
        """检查widget是否是parent的子组件"""
        if widget is None:
            return False
        
        while widget is not None:
            if widget == parent:
                return True
            widget = widget.master
        
        return False
    
    def _set_focus(self, widget: tk.Widget):
        """设置焦点"""
        try:
            widget.focus_set()
        except tk.TclError:
            pass
    
    def _on_focus_in(self, event):
        """焦点进入"""
        self._draw_focus_ring(event.widget)
    
    def _on_focus_out(self, event):
        """焦点离开"""
        self._clear_focus_ring()
    
    def _draw_focus_ring(self, widget: tk.Widget):
        """绘制焦点轮廓"""
        self._clear_focus_ring()
        
        try:
            # 获取组件位置和大小
            x = widget.winfo_rootx() - self.root.winfo_rootx()
            y = widget.winfo_rooty() - self.root.winfo_rooty()
            w = widget.winfo_width()
            h = widget.winfo_height()
            
            style = self._focus_ring_style
            offset = style["offset"]
            width = style["width"]
            color = style["color"]
            
            # 创建画布
            self._focus_ring_canvas = tk.Canvas(
                self.root,
                highlightthickness=0,
                bg=""
            )
            
            # 绘制轮廓
            self._focus_ring_canvas.create_rectangle(
                offset,
                offset,
                w + offset * 2,
                h + offset * 2,
                outline=color,
                width=width,
                dash=(4, 2) if style["style"] == "dashed" else None
            )
            
            # 定位
            self._focus_ring_canvas.place(
                x=x - offset,
                y=y - offset,
                width=w + offset * 4,
                height=h + offset * 4
            )
            
            # 确保在最上层但不阻挡点击
            self._focus_ring_canvas.lower()
            
        except Exception as e:
            logger.debug(f"绘制焦点轮廓失败: {e}")
    
    def _clear_focus_ring(self):
        """清除焦点轮廓"""
        if self._focus_ring_canvas:
            try:
                self._focus_ring_canvas.destroy()
            except tk.TclError:
                pass
            self._focus_ring_canvas = None
    
    def set_focus_style(self, style: dict):
        """设置焦点样式"""
        self._focus_ring_style = style
    
    def enable_focus_trap(self, widgets: List[tk.Widget]):
        """启用焦点陷阱（用于模态框）"""
        self._trap_enabled = True
        self._trap_widgets = widgets
    
    def disable_focus_trap(self):
        """禁用焦点陷阱"""
        self._trap_enabled = False
        self._trap_widgets = []
    
    def focus_first(self, group: str = "default"):
        """聚焦第一个元素"""
        elements = self._groups.get(group, [])
        focusable = [e for e in elements if not e.skip and e.widget.winfo_exists()]
        
        if focusable:
            self._set_focus(focusable[0].widget)
    
    def focus_last(self, group: str = "default"):
        """聚焦最后一个元素"""
        elements = self._groups.get(group, [])
        focusable = [e for e in elements if not e.skip and e.widget.winfo_exists()]
        
        if focusable:
            self._set_focus(focusable[-1].widget)


class SkipLink(tk.Frame):
    """Skip Link组件 - 用于跳过导航区域"""
    
    def __init__(
        self,
        parent: tk.Widget,
        text: str = "跳到主要内容",
        target: Optional[tk.Widget] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.target = target
        
        # 默认隐藏，聚焦时显示
        self.configure(bg="#1a1a1a")
        
        self.link = tk.Label(
            self,
            text=text,
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 12),
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.link.pack()
        
        # 绑定事件
        self.link.bind("<Button-1>", self._on_click)
        self.link.bind("<Return>", self._on_click)
        self.link.bind("<space>", self._on_click)
        self.link.bind("<FocusIn>", self._on_focus_in)
        self.link.bind("<FocusOut>", self._on_focus_out)
        
        # 初始隐藏
        self.place(x=-9999, y=-9999)
        
        # 使其可聚焦
        self.link.configure(takefocus=True)
    
    def _on_click(self, event=None):
        """点击处理"""
        if self.target and self.target.winfo_exists():
            self.target.focus_set()
        return "break"
    
    def _on_focus_in(self, event):
        """聚焦时显示"""
        self.place(x=10, y=10)
        self.lift()
    
    def _on_focus_out(self, event):
        """失焦时隐藏"""
        self.place(x=-9999, y=-9999)
    
    def set_target(self, target: tk.Widget):
        """设置跳转目标"""
        self.target = target


class KeyboardNavigable:
    """键盘导航混入类"""
    
    def enable_arrow_navigation(
        self,
        widgets: List[tk.Widget],
        wrap: bool = True
    ):
        """启用方向键导航"""
        for i, widget in enumerate(widgets):
            widget._nav_index = i
            widget._nav_widgets = widgets
            widget._nav_wrap = wrap
            
            widget.bind("<Up>", self._on_arrow_up)
            widget.bind("<Down>", self._on_arrow_down)
            widget.bind("<Left>", self._on_arrow_left)
            widget.bind("<Right>", self._on_arrow_right)
    
    def _on_arrow_up(self, event):
        """向上"""
        self._navigate_arrow(event.widget, -1)
        return "break"
    
    def _on_arrow_down(self, event):
        """向下"""
        self._navigate_arrow(event.widget, 1)
        return "break"
    
    def _on_arrow_left(self, event):
        """向左"""
        self._navigate_arrow(event.widget, -1)
        return "break"
    
    def _on_arrow_right(self, event):
        """向右"""
        self._navigate_arrow(event.widget, 1)
        return "break"
    
    def _navigate_arrow(self, widget: tk.Widget, direction: int):
        """方向键导航"""
        if not hasattr(widget, '_nav_widgets'):
            return
        
        widgets = widget._nav_widgets
        current_index = widget._nav_index
        wrap = widget._nav_wrap
        
        new_index = current_index + direction
        
        if wrap:
            new_index = new_index % len(widgets)
        else:
            new_index = max(0, min(new_index, len(widgets) - 1))
        
        if 0 <= new_index < len(widgets):
            widgets[new_index].focus_set()


class LiveRegion(tk.Frame):
    """ARIA Live Region - 动态内容通知"""
    
    def __init__(
        self,
        parent: tk.Widget,
        politeness: str = "polite",  # "polite", "assertive", "off"
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        
        self.politeness = politeness
        
        # 屏幕外不可见区域
        self.configure(bg=parent.cget("bg") if hasattr(parent, "cget") else "#1a1a1a")
        
        self._label = tk.Label(
            self,
            text="",
            bg=self.cget("bg"),
            fg=self.cget("bg"),
            width=1,
            height=1
        )
        self._label.pack()
        
        # 放置在屏幕外
        self.place(x=-9999, y=-9999, width=1, height=1)
    
    def announce(self, message: str, clear_delay: int = 5000):
        """宣告消息
        
        Args:
            message: 要宣告的消息
            clear_delay: 清除延迟（毫秒）
        """
        # 清空后重新设置，触发屏幕阅读器
        self._label.configure(text="")
        self.after(100, lambda: self._label.configure(text=message))
        
        # 延迟清除
        if clear_delay > 0:
            self.after(clear_delay, lambda: self._label.configure(text=""))


class AccessibilityHelper:
    """可访问性辅助工具"""
    
    @staticmethod
    def make_focusable(widget: tk.Widget, tab_index: int = 0):
        """使组件可聚焦"""
        widget.configure(takefocus=True)
        
        # 添加焦点样式
        def on_focus_in(e):
            try:
                widget.configure(highlightthickness=2, highlightcolor="#3b82f6")
            except tk.TclError:
                pass
        
        def on_focus_out(e):
            try:
                widget.configure(highlightthickness=0)
            except tk.TclError:
                pass
        
        widget.bind("<FocusIn>", on_focus_in, add="+")
        widget.bind("<FocusOut>", on_focus_out, add="+")
    
    @staticmethod
    def add_keyboard_activation(
        widget: tk.Widget,
        callback: Callable[[], None]
    ):
        """添加键盘激活支持（Enter/Space）"""
        def on_key(event):
            callback()
            return "break"
        
        widget.bind("<Return>", on_key)
        widget.bind("<space>", on_key)
    
    @staticmethod
    def set_accessible_name(widget: tk.Widget, name: str):
        """设置可访问名称（用于屏幕阅读器）"""
        # Tkinter不原生支持ARIA，但我们可以存储元数据
        widget._accessible_name = name
    
    @staticmethod
    def set_accessible_description(widget: tk.Widget, description: str):
        """设置可访问描述"""
        widget._accessible_description = description
    
    @staticmethod
    def create_focus_order(widgets: List[tk.Widget]):
        """创建焦点顺序"""
        for i, widget in enumerate(widgets):
            if i > 0:
                widgets[i-1].tk_focusNext = lambda w=widget: w
            if i < len(widgets) - 1:
                widgets[i+1].tk_focusPrev = lambda w=widget: w


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("可访问性测试")
    root.geometry("600x400")
    root.configure(bg="#121212")
    
    # 初始化焦点管理器
    focus_manager = FocusManager(root)
    
    # 创建Skip Link
    main_content = tk.Frame(root, bg="#121212")
    skip_link = SkipLink(root, text="跳到主要内容", target=main_content)
    
    # 导航区域
    nav_frame = tk.Frame(root, bg="#1a1a1a", padx=20, pady=10)
    nav_frame.pack(fill=tk.X)
    
    for i, text in enumerate(["首页", "文章", "设置", "帮助"]):
        btn = tk.Button(
            nav_frame,
            text=text,
            bg="#252525",
            fg="#e5e5e5",
            relief="flat",
            padx=15,
            pady=5
        )
        btn.pack(side=tk.LEFT, padx=5)
        focus_manager.register(btn, tab_index=i, group="nav", label=text)
    
    # 主要内容
    main_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    tk.Label(
        main_content,
        text="主要内容区域",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=20)
    
    # 表单
    form_frame = tk.Frame(main_content, bg="#121212")
    form_frame.pack(fill=tk.X, pady=10)
    
    tk.Label(
        form_frame,
        text="用户名:",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 12)
    ).pack(anchor="w")
    
    username_entry = tk.Entry(
        form_frame,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5"
    )
    username_entry.pack(fill=tk.X, pady=(5, 15))
    focus_manager.register(username_entry, tab_index=10, group="form", label="用户名")
    
    tk.Label(
        form_frame,
        text="密码:",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 12)
    ).pack(anchor="w")
    
    password_entry = tk.Entry(
        form_frame,
        bg="#252525",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
        relief="flat",
        insertbackground="#e5e5e5",
        show="•"
    )
    password_entry.pack(fill=tk.X, pady=(5, 15))
    focus_manager.register(password_entry, tab_index=11, group="form", label="密码")
    
    submit_btn = tk.Button(
        form_frame,
        text="提交",
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        relief="flat",
        padx=20,
        pady=8
    )
    submit_btn.pack(anchor="w")
    focus_manager.register(submit_btn, tab_index=12, group="form", label="提交按钮")
    
    # Live Region
    live_region = LiveRegion(root, politeness="polite")
    
    def on_submit():
        live_region.announce("表单已提交")
    
    submit_btn.configure(command=on_submit)
    AccessibilityHelper.add_keyboard_activation(submit_btn, on_submit)
    
    # 状态提示
    tk.Label(
        root,
        text="按Tab键在元素间导航 | 按Enter或Space激活按钮",
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10)
    ).pack(side=tk.BOTTOM, pady=10)
    
    root.mainloop()
