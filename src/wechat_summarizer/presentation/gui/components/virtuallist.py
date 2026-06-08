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

import logging
import time
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from typing import Any

from .virtuallist_models import (
    MAX_ITEM_HEIGHT,
    MAX_ITEMS,
    MIN_ITEM_HEIGHT,
    RENDER_TIMEOUT_MS,
    SCROLL_THROTTLE_MS,
    VirtualItem,
)
from .virtuallist_render import VirtualListRenderMixin

logger = logging.getLogger(__name__)


class VirtualList(VirtualListRenderMixin, tk.Frame):
    """虚拟列表组件

    只渲染可见区域的列表项，支持大数据量(10万+)
    """

    def __init__(
        self,
        parent: tk.Misc,
        item_height: int = 40,
        render_item: Callable[[tk.Frame, Any, int], tk.Widget] | None = None,
        on_item_click: Callable[[int, Any], None] | None = None,
        on_load_more: Callable[[], None] | None = None,
        load_more_threshold: int = 5,
        **kwargs,
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
        self._data: list[Any] = []
        self._items: dict[int, VirtualItem] = {}
        self._item_heights: dict[int, int] = {}  # 动态高度缓存

        # 渲染状态
        self._visible_range: tuple[int, int] = (0, 0)
        self._rendered_widgets: dict[int, tk.Widget] = {}
        self._scroll_position = 0
        self._total_height = 0

        # 节流控制
        self._last_scroll_time = 0
        self._scroll_scheduled = False
        self._is_loading_more = False

        # 样式
        self._bg = bg
        self._selected_index: int | None = None
        self._hover_index: int | None = None

        self._setup_ui()

    def _setup_ui(self):
        """构建UI"""
        # 滚动容器
        self._canvas = tk.Canvas(self, bg=self._bg, highlightthickness=0, bd=0)

        # 滚动条
        self._scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._on_scroll_command)

        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        # 布局
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 内容容器
        self._content = tk.Frame(self._canvas, bg=self._bg)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._content, anchor=tk.NW)

        # 绑定事件
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)
        self._content.bind("<Configure>", self._on_content_configure)

    def set_data(self, data: list[Any]):
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

    def append_data(self, items: list[Any]):
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
            self._items[i] = VirtualItem(index=i, data=self._data[i], height=height, y_offset=total)
            total += height

        self._total_height = total

        # 更新内容高度
        self._content.configure(height=self._total_height)
        self._canvas.configure(scrollregion=(0, 0, self._canvas.winfo_width(), self._total_height))

    def _get_visible_range(self) -> tuple[int, int]:
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
            candidate = self._items.get(i)
            if candidate and candidate.y_offset > scroll_bottom:
                end_index = min(len(self._data), i + 2)
                break

        return (start_index, end_index)

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

    def get_selected_index(self) -> int | None:
        """获取选中索引"""
        return self._selected_index

    def get_selected_data(self) -> Any | None:
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


__all__ = [
    "MAX_ITEMS",
    "MAX_ITEM_HEIGHT",
    "MIN_ITEM_HEIGHT",
    "RENDER_TIMEOUT_MS",
    "SCROLL_THROTTLE_MS",
    "VirtualItem",
    "VirtualList",
]
