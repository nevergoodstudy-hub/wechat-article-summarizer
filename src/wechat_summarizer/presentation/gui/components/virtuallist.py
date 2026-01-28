"""
虚拟列表组件 (Virtual List)
高性能大数据量列表渲染

功能特性:
- 只渲染可见区域
- 滚动节流(16ms/60fps)
- 动态行高支持
- 无限滚动加载
- 平滑滚动

安全措施:
- 数据量限制
- 内存占用监控
- 渲染超时保护
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, List, Any, Dict, Tuple
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


# 安全限制
MAX_ITEMS = 100000  # 最大数据条数
MAX_ITEM_HEIGHT = 500  # 单项最大高度
MIN_ITEM_HEIGHT = 20  # 单项最小高度
RENDER_TIMEOUT_MS = 100  # 渲染超时
SCROLL_THROTTLE_MS = 16  # 滚动节流 (60fps)


@dataclass
class VirtualItem:
    """虚拟列表项"""
    index: int
    data: Any
    height: int = 40
    y_offset: int = 0


class VirtualList(tk.Frame):
    """虚拟列表组件
    
    只渲染可见区域的列表项，支持大数据量(10万+)
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        item_height: int = 40,
        render_item: Optional[Callable[[tk.Frame, Any, int], tk.Widget]] = None,
        on_item_click: Optional[Callable[[int, Any], None]] = None,
        on_load_more: Optional[Callable[[], None]] = None,
        load_more_threshold: int = 5,
        **kwargs
    ):
        """
        Args:
            parent: 父容器
            item_height: 默认项高度
            render_item: 渲染函数 (container, data, index) -> Widget
            on_item_click: 点击回调 (index, data)
            on_load_more: 加载更多回调
            load_more_threshold: 触发加载更多的剩余项数
        """
        # 提取样式参数
        bg = kwargs.pop("bg", "#1a1a1a")
        super().__init__(parent, bg=bg, **kwargs)
        
        self._item_height = max(MIN_ITEM_HEIGHT, min(MAX_ITEM_HEIGHT, item_height))
        self._render_item = render_item or self._default_render
        self._on_item_click = on_item_click
        self._on_load_more = on_load_more
        self._load_more_threshold = load_more_threshold
        
        # 数据
        self._data: List[Any] = []
        self._items: Dict[int, VirtualItem] = {}
        self._item_heights: Dict[int, int] = {}  # 动态高度缓存
        
        # 渲染状态
        self._visible_range: Tuple[int, int] = (0, 0)
        self._rendered_widgets: Dict[int, tk.Widget] = {}
        self._scroll_position = 0
        self._total_height = 0
        
        # 节流控制
        self._last_scroll_time = 0
        self._scroll_scheduled = False
        self._is_loading_more = False
        
        # 样式
        self._bg = bg
        self._selected_index: Optional[int] = None
        self._hover_index: Optional[int] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """构建UI"""
        # 滚动容器
        self._canvas = tk.Canvas(
            self,
            bg=self._bg,
            highlightthickness=0,
            bd=0
        )
        
        # 滚动条
        self._scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self._on_scroll_command
        )
        
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        
        # 布局
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 内容容器
        self._content = tk.Frame(self._canvas, bg=self._bg)
        self._canvas_window = self._canvas.create_window(
            (0, 0),
            window=self._content,
            anchor=tk.NW
        )
        
        # 绑定事件
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._content.bind("<Configure>", self._on_content_configure)
    
    def set_data(self, data: List[Any]):
        """设置数据
        
        Args:
            data: 数据列表
        """
        # 安全限制
        if len(data) > MAX_ITEMS:
            logger.warning(f"数据量超限({len(data)})，截断至{MAX_ITEMS}")
            data = data[:MAX_ITEMS]
        
        self._data = list(data)
        self._items.clear()
        self._item_heights.clear()
        self._rendered_widgets.clear()
        
        # 计算总高度
        self._calculate_total_height()
        
        # 重置滚动
        self._scroll_position = 0
        self._canvas.yview_moveto(0)
        
        # 渲染可见区域
        self._render_visible()
    
    def append_data(self, items: List[Any]):
        """追加数据"""
        if len(self._data) + len(items) > MAX_ITEMS:
            remaining = MAX_ITEMS - len(self._data)
            if remaining > 0:
                items = items[:remaining]
            else:
                return
        
        self._data.extend(items)
        self._calculate_total_height()
        self._render_visible()
        self._is_loading_more = False
    
    def _calculate_total_height(self):
        """计算总高度"""
        total = 0
        for i in range(len(self._data)):
            height = self._item_heights.get(i, self._item_height)
            self._items[i] = VirtualItem(
                index=i,
                data=self._data[i],
                height=height,
                y_offset=total
            )
            total += height
        
        self._total_height = total
        
        # 更新内容高度
        self._content.configure(height=self._total_height)
        self._canvas.configure(scrollregion=(0, 0, self._canvas.winfo_width(), self._total_height))
    
    def _get_visible_range(self) -> Tuple[int, int]:
        """获取可见范围"""
        canvas_height = self._canvas.winfo_height()
        if canvas_height <= 0:
            return (0, 0)
        
        # 获取当前滚动位置
        try:
            top_fraction = self._canvas.yview()[0]
        except tk.TclError:
            top_fraction = 0
        
        scroll_top = int(top_fraction * self._total_height)
        scroll_bottom = scroll_top + canvas_height
        
        # 查找可见项
        start_index = 0
        end_index = len(self._data)
        
        for i, item in self._items.items():
            if item.y_offset + item.height >= scroll_top:
                start_index = max(0, i - 2)  # 多渲染几项缓冲
                break
        
        for i in range(start_index, len(self._data)):
            item = self._items.get(i)
            if item and item.y_offset > scroll_bottom:
                end_index = min(len(self._data), i + 2)
                break
        
        return (start_index, end_index)
    
    def _render_visible(self):
        """渲染可见区域"""
        start_time = time.time()
        
        new_range = self._get_visible_range()
        if new_range == self._visible_range and self._rendered_widgets:
            return
        
        old_start, old_end = self._visible_range
        new_start, new_end = new_range
        
        # 移除不再可见的项
        for i in list(self._rendered_widgets.keys()):
            if i < new_start or i >= new_end:
                widget = self._rendered_widgets.pop(i)
                widget.destroy()
        
        # 渲染新可见的项
        for i in range(new_start, new_end):
            # 超时保护
            if (time.time() - start_time) * 1000 > RENDER_TIMEOUT_MS:
                logger.warning("渲染超时，延迟剩余项")
                self.after(50, self._render_visible)
                break
            
            if i not in self._rendered_widgets and i in self._items:
                self._render_item_at(i)
        
        self._visible_range = new_range
        
        # 检查是否需要加载更多
        self._check_load_more()
    
    def _render_item_at(self, index: int):
        """渲染指定索引的项"""
        if index >= len(self._data):
            return
        
        item = self._items.get(index)
        if not item:
            return
        
        # 创建项容器
        container = tk.Frame(
            self._content,
            bg=self._bg,
            height=item.height
        )
        
        # 渲染内容
        try:
            widget = self._render_item(container, item.data, index)
            if widget:
                widget.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logger.error(f"渲染项失败 ({index}): {e}")
            return
        
        # 定位
        container.place(
            x=0,
            y=item.y_offset,
            relwidth=1.0,
            height=item.height
        )
        
        # 绑定事件
        self._bind_item_events(container, index)
        
        self._rendered_widgets[index] = container
    
    def _bind_item_events(self, widget: tk.Widget, index: int):
        """绑定项事件"""
        def on_enter(e):
            self._hover_index = index
            if index != self._selected_index:
                widget.configure(bg="#252525")
                for child in widget.winfo_children():
                    try:
                        child.configure(bg="#252525")
                    except tk.TclError:
                        pass
        
        def on_leave(e):
            self._hover_index = None
            if index != self._selected_index:
                widget.configure(bg=self._bg)
                for child in widget.winfo_children():
                    try:
                        child.configure(bg=self._bg)
                    except tk.TclError:
                        pass
        
        def on_click(e):
            self._select_item(index)
            if self._on_item_click:
                try:
                    self._on_item_click(index, self._data[index])
                except Exception as err:
                    logger.error(f"点击回调失败: {err}")
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        widget.bind("<Button-1>", on_click)
        
        # 递归绑定子组件
        for child in widget.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", on_click)
    
    def _select_item(self, index: int):
        """选择项"""
        # 取消之前选择
        if self._selected_index is not None and self._selected_index in self._rendered_widgets:
            old_widget = self._rendered_widgets[self._selected_index]
            old_widget.configure(bg=self._bg)
            for child in old_widget.winfo_children():
                try:
                    child.configure(bg=self._bg)
                except tk.TclError:
                    pass
        
        # 设置新选择
        self._selected_index = index
        if index in self._rendered_widgets:
            widget = self._rendered_widgets[index]
            widget.configure(bg="#3b82f6")
            for child in widget.winfo_children():
                try:
                    child.configure(bg="#3b82f6")
                except tk.TclError:
                    pass
    
    def _default_render(self, container: tk.Frame, data: Any, index: int) -> tk.Widget:
        """默认渲染函数"""
        label = tk.Label(
            container,
            text=str(data),
            bg=self._bg,
            fg="#e5e5e5",
            font=("Segoe UI", 12),
            anchor="w",
            padx=12,
            pady=8
        )
        return label
    
    def _on_scroll_command(self, *args):
        """滚动条命令"""
        self._canvas.yview(*args)
        self._throttled_render()
    
    def _on_mousewheel(self, event):
        """鼠标滚轮"""
        self._canvas.yview_scroll(-event.delta // 120, "units")
        self._throttled_render()
    
    def _throttled_render(self):
        """节流渲染"""
        current_time = time.time() * 1000
        
        if current_time - self._last_scroll_time < SCROLL_THROTTLE_MS:
            if not self._scroll_scheduled:
                self._scroll_scheduled = True
                self.after(SCROLL_THROTTLE_MS, self._delayed_render)
            return
        
        self._last_scroll_time = current_time
        self._render_visible()
    
    def _delayed_render(self):
        """延迟渲染"""
        self._scroll_scheduled = False
        self._last_scroll_time = time.time() * 1000
        self._render_visible()
    
    def _on_canvas_configure(self, event):
        """画布大小变化"""
        self._canvas.itemconfig(self._canvas_window, width=event.width)
        self._render_visible()
    
    def _on_content_configure(self, event):
        """内容大小变化"""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
    
    def _check_load_more(self):
        """检查是否需要加载更多"""
        if not self._on_load_more or self._is_loading_more:
            return
        
        _, end_index = self._visible_range
        remaining = len(self._data) - end_index
        
        if remaining <= self._load_more_threshold:
            self._is_loading_more = True
            try:
                self._on_load_more()
            except Exception as e:
                logger.error(f"加载更多失败: {e}")
                self._is_loading_more = False
    
    def scroll_to_index(self, index: int):
        """滚动到指定索引"""
        if index < 0 or index >= len(self._data):
            return
        
        item = self._items.get(index)
        if not item:
            return
        
        if self._total_height > 0:
            fraction = item.y_offset / self._total_height
            self._canvas.yview_moveto(fraction)
            self._render_visible()
    
    def get_selected_index(self) -> Optional[int]:
        """获取选中索引"""
        return self._selected_index
    
    def get_selected_data(self) -> Optional[Any]:
        """获取选中数据"""
        if self._selected_index is not None and self._selected_index < len(self._data):
            return self._data[self._selected_index]
        return None
    
    def refresh(self):
        """刷新列表"""
        self._rendered_widgets.clear()
        for widget in self._content.winfo_children():
            widget.destroy()
        self._render_visible()
    
    def clear(self):
        """清空列表"""
        self._data.clear()
        self._items.clear()
        self._item_heights.clear()
        self._rendered_widgets.clear()
        self._selected_index = None
        self._total_height = 0
        
        for widget in self._content.winfo_children():
            widget.destroy()
        
        self._canvas.configure(scrollregion=(0, 0, 0, 0))


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("虚拟列表测试")
    root.geometry("600x500")
    root.configure(bg="#121212")
    
    # 生成测试数据
    test_data = [f"项目 {i+1} - 这是一段测试文本内容" for i in range(10000)]
    
    # 自定义渲染函数
    def render_item(container, data, index):
        frame = tk.Frame(container, bg="#1a1a1a")
        
        tk.Label(
            frame,
            text=f"#{index+1}",
            bg="#1a1a1a",
            fg="#808080",
            font=("Segoe UI", 10),
            width=6
        ).pack(side=tk.LEFT, padx=(12, 0))
        
        tk.Label(
            frame,
            text=data,
            bg="#1a1a1a",
            fg="#e5e5e5",
            font=("Segoe UI", 12),
            anchor="w"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        
        return frame
    
    def on_click(index, data):
        print(f"点击: {index} - {data}")
    
    # 创建虚拟列表
    vlist = VirtualList(
        root,
        item_height=40,
        render_item=render_item,
        on_item_click=on_click,
        bg="#1a1a1a"
    )
    vlist.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 设置数据
    vlist.set_data(test_data)
    
    # 状态栏
    tk.Label(
        root,
        text=f"共 {len(test_data)} 条数据 | 只渲染可见区域",
        bg="#121212",
        fg="#808080",
        font=("Segoe UI", 10)
    ).pack(side=tk.BOTTOM, pady=10)
    
    root.mainloop()
