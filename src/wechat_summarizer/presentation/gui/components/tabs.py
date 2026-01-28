"""现代标签页组件 - 2026 UI设计趋势

提供：
- 滑动指示器动画
- 可关闭标签
- 拖拽排序
- 键盘导航

安全审查：
- 标签数量限制
- 拖拽边界检查
- 事件清理
"""
from __future__ import annotations

import tkinter as tk
from enum import Enum
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass
import html

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors
from ..styles.typography import get_text_style, TextStyles


class TabPosition(Enum):
    """标签位置"""
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class TabItem:
    """标签项数据"""
    id: str
    label: str
    closable: bool = True
    icon: Optional[Any] = None
    content: Optional[tk.Widget] = None
    disabled: bool = False


class TabIndicator:
    """滑动指示器动画组件
    
    在活动标签下方绘制滑动条。
    
    安全措施:
    - 动画资源自动清理
    - 位置边界检查
    """
    
    def __init__(
        self,
        canvas: tk.Canvas,
        color: str,
        height: int = 3,
        animation_duration: int = 200
    ):
        """初始化指示器
        
        Args:
            canvas: 绘制画布
            color: 指示器颜色
            height: 指示器高度
            animation_duration: 动画时长(ms)
        """
        self._canvas = canvas
        self._color = color
        self._height = max(1, min(height, 10))
        self._duration = max(50, min(animation_duration, 500))
        self._animation_id = None
        
        # 当前位置
        self._x = 0
        self._width = 0
        self._target_x = 0
        self._target_width = 0
        
        # 绘制初始指示器
        self._indicator_id = self._canvas.create_rectangle(
            0, 0, 0, 0,
            fill=color,
            outline="",
            tags="indicator"
        )
    
    def move_to(self, x: int, width: int, y: int):
        """移动到目标位置
        
        Args:
            x: 目标X坐标
            width: 目标宽度
            y: Y坐标
        """
        self._target_x = max(0, x)
        self._target_width = max(0, width)
        self._y = y
        
        self._animate()
    
    def _animate(self):
        """执行动画"""
        if self._animation_id:
            try:
                self._canvas.after_cancel(self._animation_id)
            except Exception:
                pass
        
        steps = self._duration // 16
        if steps <= 0:
            steps = 1
        
        start_x = self._x
        start_width = self._width
        delta_x = self._target_x - start_x
        delta_width = self._target_width - start_width
        current_step = [0]
        
        def animate_step():
            if current_step[0] >= steps:
                self._x = self._target_x
                self._width = self._target_width
                self._update_rect()
                return
            
            progress = current_step[0] / steps
            # 缓动函数 (ease-in-out)
            eased = progress * progress * (3 - 2 * progress)
            
            self._x = start_x + delta_x * eased
            self._width = start_width + delta_width * eased
            self._update_rect()
            
            current_step[0] += 1
            self._animation_id = self._canvas.after(16, animate_step)
        
        animate_step()
    
    def _update_rect(self):
        """更新矩形位置"""
        self._canvas.coords(
            self._indicator_id,
            self._x, self._y,
            self._x + self._width, self._y + self._height
        )
    
    def set_color(self, color: str):
        """设置颜色"""
        self._color = color
        self._canvas.itemconfig(self._indicator_id, fill=color)
    
    def destroy(self):
        """销毁"""
        if self._animation_id:
            try:
                self._canvas.after_cancel(self._animation_id)
            except Exception:
                pass
        self._canvas.delete(self._indicator_id)


class ModernTabs(tk.Frame):
    """现代标签页组件
    
    特性：
    - 滑动指示器动画
    - 可关闭标签
    - 拖拽排序
    - 键盘导航
    
    安全措施:
    - 标签数量限制
    - 拖拽边界检查
    - 标签文本XSS防护
    """
    
    MAX_TABS = 50  # 最大标签数量
    MAX_LABEL_LENGTH = 50  # 最大标签文本长度
    
    def __init__(
        self,
        master,
        position: TabPosition = TabPosition.TOP,
        closable: bool = True,
        draggable: bool = True,
        on_tab_change: Optional[Callable[[str], None]] = None,
        on_tab_close: Optional[Callable[[str], bool]] = None,
        on_tab_reorder: Optional[Callable[[List[str]], None]] = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化标签页组件
        
        Args:
            master: 父容器
            position: 标签位置
            closable: 是否可关闭
            draggable: 是否可拖拽
            on_tab_change: 标签切换回调
            on_tab_close: 标签关闭回调 (返回False阻止关闭)
            on_tab_reorder: 标签重排序回调
            theme: 主题
            **kwargs: 其他参数
        """
        self._theme = theme
        self._colors = self._get_colors(theme)
        
        super().__init__(master, bg=self._colors['bg'], **kwargs)
        
        self._position = position
        self._closable = closable
        self._draggable = draggable
        self._on_tab_change = on_tab_change
        self._on_tab_close = on_tab_close
        self._on_tab_reorder = on_tab_reorder
        
        # 标签数据
        self._tabs: List[TabItem] = []
        self._active_tab_id: Optional[str] = None
        self._tab_buttons: Dict[str, tk.Widget] = {}
        
        # 拖拽状态
        self._drag_data = {
            'tab_id': None,
            'start_x': 0,
            'start_index': 0
        }
        
        # 创建UI
        self._setup_ui()
    
    def _get_colors(self, theme: str) -> dict:
        """获取颜色配置 (Tkinter兼容版本)"""
        if theme == "dark":
            return {
                'bg': ModernColors.DARK_BG,
                'tab_bar_bg': ModernColors.DARK_CARD,
                'tab_bg': ModernColors.DARK_CARD,  # Tkinter不支持transparent
                'tab_active_bg': ModernColors.DARK_BG_SECONDARY,
                'tab_hover_bg': ModernColors.DARK_CARD_HOVER,
                'text': ModernColors.DARK_TEXT,
                'text_secondary': ModernColors.DARK_TEXT_SECONDARY,
                'text_disabled': ModernColors.DARK_TEXT_DISABLED,
                'indicator': ModernColors.DARK_ACCENT,
                'close_hover': ModernColors.ERROR,
                'border': ModernColors.DARK_BORDER,
            }
        else:
            return {
                'bg': ModernColors.LIGHT_BG,
                'tab_bar_bg': ModernColors.LIGHT_CARD,
                'tab_bg': ModernColors.LIGHT_CARD,  # Tkinter不支持transparent
                'tab_active_bg': ModernColors.LIGHT_BG_SECONDARY,
                'tab_hover_bg': ModernColors.LIGHT_CARD_HOVER,
                'text': ModernColors.LIGHT_TEXT,
                'text_secondary': ModernColors.LIGHT_TEXT_SECONDARY,
                'text_disabled': ModernColors.LIGHT_TEXT_DISABLED,
                'indicator': ModernColors.LIGHT_ACCENT,
                'close_hover': ModernColors.ERROR,
                'border': ModernColors.LIGHT_BORDER,
            }
    
    def _setup_ui(self):
        """构建UI"""
        # 标签栏容器
        self._tab_bar_frame = tk.Frame(self, bg=self._colors['tab_bar_bg'])
        
        # 标签栏Canvas（用于绘制指示器）
        self._tab_bar_canvas = tk.Canvas(
            self._tab_bar_frame,
            bg=self._colors['tab_bar_bg'],
            highlightthickness=0,
            height=40
        )
        self._tab_bar_canvas.pack(fill="x", expand=True)
        
        # 标签按钮容器
        self._tabs_container = tk.Frame(
            self._tab_bar_canvas,
            bg=self._colors['tab_bar_bg']
        )
        self._tab_bar_canvas.create_window(
            0, 0,
            window=self._tabs_container,
            anchor="nw"
        )
        
        # 创建滑动指示器
        self._indicator = TabIndicator(
            self._tab_bar_canvas,
            color=self._colors['indicator'],
            height=3,
            animation_duration=200
        )
        
        # 内容区域
        self._content_frame = tk.Frame(self, bg=self._colors['bg'])
        
        # 布局
        if self._position == TabPosition.TOP:
            self._tab_bar_frame.pack(fill="x", side="top")
            self._content_frame.pack(fill="both", expand=True, side="top")
        elif self._position == TabPosition.BOTTOM:
            self._content_frame.pack(fill="both", expand=True, side="top")
            self._tab_bar_frame.pack(fill="x", side="bottom")
        # TODO: LEFT/RIGHT 布局
        
        # 键盘绑定
        self.bind_all("<Control-Tab>", self._on_ctrl_tab)
        self.bind_all("<Control-Shift-Tab>", self._on_ctrl_shift_tab)
    
    def add_tab(
        self,
        tab_id: str,
        label: str,
        content: Optional[tk.Widget] = None,
        closable: Optional[bool] = None,
        icon: Optional[Any] = None,
        select: bool = True
    ) -> bool:
        """添加标签
        
        Args:
            tab_id: 标签ID
            label: 标签文本
            content: 内容组件
            closable: 是否可关闭 (None使用全局设置)
            icon: 图标
            select: 是否选中
            
        Returns:
            是否添加成功
        """
        # 数量限制
        if len(self._tabs) >= self.MAX_TABS:
            return False
        
        # ID唯一性检查
        if any(t.id == tab_id for t in self._tabs):
            return False
        
        # 文本安全处理
        label = html.escape(label[:self.MAX_LABEL_LENGTH])
        
        # 创建标签数据
        tab = TabItem(
            id=tab_id,
            label=label,
            closable=closable if closable is not None else self._closable,
            icon=icon,
            content=content
        )
        self._tabs.append(tab)
        
        # 创建标签按钮
        self._create_tab_button(tab)
        
        # 选中
        if select or self._active_tab_id is None:
            self.select_tab(tab_id)
        
        return True
    
    def _create_tab_button(self, tab: TabItem):
        """创建标签按钮"""
        # 按钮容器
        btn_frame = tk.Frame(
            self._tabs_container,
            bg=self._colors['tab_bg']
        )
        btn_frame.pack(side="left", padx=2, pady=(4, 0))
        
        # 标签文本按钮
        if _CTK_AVAILABLE:
            label_btn = ctk.CTkButton(
                btn_frame,
                text=tab.label,
                fg_color="transparent",
                hover_color=self._colors['tab_hover_bg'],
                text_color=self._colors['text_secondary'],
                corner_radius=6,
                height=32,
                font=get_text_style(TextStyles.BODY),
                command=lambda: self.select_tab(tab.id)
            )
        else:
            label_btn = tk.Button(
                btn_frame,
                text=tab.label,
                bg=self._colors['tab_bg'] if self._colors['tab_bg'] != 'transparent' else self._colors['tab_bar_bg'],
                fg=self._colors['text_secondary'],
                relief="flat",
                font=get_text_style(TextStyles.BODY),
                command=lambda: self.select_tab(tab.id),
                cursor="hand2"
            )
            label_btn.bind("<Enter>", lambda e, b=label_btn: b.configure(
                bg=self._colors['tab_hover_bg']
            ))
            label_btn.bind("<Leave>", lambda e, b=label_btn, tid=tab.id: b.configure(
                bg=self._colors['tab_active_bg'] if tid == self._active_tab_id else self._colors['tab_bar_bg']
            ))
        
        label_btn.pack(side="left", padx=(8, 0 if tab.closable else 8))
        
        # 关闭按钮
        close_btn = None
        if tab.closable:
            if _CTK_AVAILABLE:
                close_btn = ctk.CTkButton(
                    btn_frame,
                    text="×",
                    width=20,
                    height=20,
                    fg_color="transparent",
                    hover_color=self._colors['close_hover'],
                    text_color=self._colors['text_secondary'],
                    corner_radius=10,
                    font=("Arial", 12),
                    command=lambda: self.close_tab(tab.id)
                )
            else:
                close_btn = tk.Button(
                    btn_frame,
                    text="×",
                    width=2,
                    bg=self._colors['tab_bar_bg'],
                    fg=self._colors['text_secondary'],
                    relief="flat",
                    font=("Arial", 10),
                    command=lambda: self.close_tab(tab.id),
                    cursor="hand2"
                )
                close_btn.bind("<Enter>", lambda e, b=close_btn: b.configure(
                    bg=self._colors['close_hover'],
                    fg="#FFFFFF"
                ))
                close_btn.bind("<Leave>", lambda e, b=close_btn: b.configure(
                    bg=self._colors['tab_bar_bg'],
                    fg=self._colors['text_secondary']
                ))
            
            close_btn.pack(side="left", padx=(4, 8))
        
        # 拖拽绑定
        if self._draggable:
            label_btn.bind("<ButtonPress-1>", lambda e, tid=tab.id: self._on_drag_start(e, tid))
            label_btn.bind("<B1-Motion>", self._on_drag_motion)
            label_btn.bind("<ButtonRelease-1>", self._on_drag_end)
        
        # 存储引用
        self._tab_buttons[tab.id] = {
            'frame': btn_frame,
            'label': label_btn,
            'close': close_btn
        }
    
    def select_tab(self, tab_id: str):
        """选中标签
        
        Args:
            tab_id: 标签ID
        """
        tab = self._get_tab(tab_id)
        if not tab or tab.disabled:
            return
        
        # 更新活动标签
        old_id = self._active_tab_id
        self._active_tab_id = tab_id
        
        # 更新按钮样式
        self._update_tab_styles()
        
        # 更新内容
        self._update_content(tab)
        
        # 更新指示器
        self._update_indicator()
        
        # 回调
        if self._on_tab_change and old_id != tab_id:
            self._on_tab_change(tab_id)
    
    def close_tab(self, tab_id: str) -> bool:
        """关闭标签
        
        Args:
            tab_id: 标签ID
            
        Returns:
            是否关闭成功
        """
        tab = self._get_tab(tab_id)
        if not tab or not tab.closable:
            return False
        
        # 回调检查
        if self._on_tab_close:
            if not self._on_tab_close(tab_id):
                return False
        
        # 获取索引
        index = self._get_tab_index(tab_id)
        
        # 移除UI
        if tab_id in self._tab_buttons:
            self._tab_buttons[tab_id]['frame'].destroy()
            del self._tab_buttons[tab_id]
        
        # 移除数据
        self._tabs.remove(tab)
        
        # 选择相邻标签
        if self._active_tab_id == tab_id:
            if self._tabs:
                new_index = min(index, len(self._tabs) - 1)
                self.select_tab(self._tabs[new_index].id)
            else:
                self._active_tab_id = None
                self._clear_content()
        
        return True
    
    def _get_tab(self, tab_id: str) -> Optional[TabItem]:
        """获取标签数据"""
        for tab in self._tabs:
            if tab.id == tab_id:
                return tab
        return None
    
    def _get_tab_index(self, tab_id: str) -> int:
        """获取标签索引"""
        for i, tab in enumerate(self._tabs):
            if tab.id == tab_id:
                return i
        return -1
    
    def _update_tab_styles(self):
        """更新所有标签样式"""
        for tab_id, widgets in self._tab_buttons.items():
            is_active = tab_id == self._active_tab_id
            label_btn = widgets['label']
            
            if _CTK_AVAILABLE:
                if is_active:
                    label_btn.configure(
                        text_color=self._colors['text'],
                        fg_color=self._colors['tab_active_bg']
                    )
                else:
                    label_btn.configure(
                        text_color=self._colors['text_secondary'],
                        fg_color="transparent"
                    )
            else:
                if is_active:
                    label_btn.configure(
                        fg=self._colors['text'],
                        bg=self._colors['tab_active_bg']
                    )
                else:
                    label_btn.configure(
                        fg=self._colors['text_secondary'],
                        bg=self._colors['tab_bar_bg']
                    )
    
    def _update_content(self, tab: TabItem):
        """更新内容区域"""
        # 隐藏所有内容
        for child in self._content_frame.winfo_children():
            child.pack_forget()
        
        # 显示当前标签内容
        if tab.content:
            tab.content.pack(fill="both", expand=True)
    
    def _clear_content(self):
        """清空内容区域"""
        for child in self._content_frame.winfo_children():
            child.pack_forget()
    
    def _update_indicator(self):
        """更新滑动指示器"""
        if not self._active_tab_id or self._active_tab_id not in self._tab_buttons:
            return
        
        # 获取按钮位置
        btn_frame = self._tab_buttons[self._active_tab_id]['frame']
        
        # 等待布局完成
        self._tabs_container.update_idletasks()
        
        x = btn_frame.winfo_x()
        width = btn_frame.winfo_width()
        y = 37  # 指示器Y位置
        
        self._indicator.move_to(x, width, y)
    
    def _on_drag_start(self, event, tab_id: str):
        """开始拖拽"""
        self._drag_data['tab_id'] = tab_id
        self._drag_data['start_x'] = event.x_root
        self._drag_data['start_index'] = self._get_tab_index(tab_id)
    
    def _on_drag_motion(self, event):
        """拖拽中"""
        if not self._drag_data['tab_id']:
            return
        
        delta_x = event.x_root - self._drag_data['start_x']
        
        # 计算新位置
        current_index = self._get_tab_index(self._drag_data['tab_id'])
        tab_width = 100  # 估计宽度
        
        # 确定交换方向
        if abs(delta_x) > tab_width // 2:
            if delta_x > 0 and current_index < len(self._tabs) - 1:
                # 向右移动
                self._swap_tabs(current_index, current_index + 1)
                self._drag_data['start_x'] = event.x_root
            elif delta_x < 0 and current_index > 0:
                # 向左移动
                self._swap_tabs(current_index, current_index - 1)
                self._drag_data['start_x'] = event.x_root
    
    def _on_drag_end(self, event):
        """结束拖拽"""
        if self._drag_data['tab_id']:
            # 回调
            if self._on_tab_reorder:
                self._on_tab_reorder([t.id for t in self._tabs])
        
        self._drag_data['tab_id'] = None
    
    def _swap_tabs(self, index1: int, index2: int):
        """交换两个标签位置"""
        if 0 <= index1 < len(self._tabs) and 0 <= index2 < len(self._tabs):
            self._tabs[index1], self._tabs[index2] = self._tabs[index2], self._tabs[index1]
            self._rebuild_tab_bar()
    
    def _rebuild_tab_bar(self):
        """重建标签栏"""
        # 保存引用
        old_buttons = self._tab_buttons.copy()
        
        # 重新排列
        for tab in self._tabs:
            if tab.id in old_buttons:
                old_buttons[tab.id]['frame'].pack_forget()
                old_buttons[tab.id]['frame'].pack(side="left", padx=2, pady=(4, 0))
        
        # 更新指示器
        self.after(50, self._update_indicator)
    
    def _on_ctrl_tab(self, event):
        """Ctrl+Tab: 下一个标签"""
        if not self._tabs:
            return
        
        current = self._get_tab_index(self._active_tab_id)
        next_index = (current + 1) % len(self._tabs)
        self.select_tab(self._tabs[next_index].id)
    
    def _on_ctrl_shift_tab(self, event):
        """Ctrl+Shift+Tab: 上一个标签"""
        if not self._tabs:
            return
        
        current = self._get_tab_index(self._active_tab_id)
        prev_index = (current - 1) % len(self._tabs)
        self.select_tab(self._tabs[prev_index].id)
    
    def get_content_frame(self) -> tk.Frame:
        """获取内容区域Frame
        
        Returns:
            内容Frame
        """
        return self._content_frame
    
    def get_active_tab(self) -> Optional[str]:
        """获取当前活动标签ID
        
        Returns:
            标签ID或None
        """
        return self._active_tab_id
    
    def get_tabs(self) -> List[str]:
        """获取所有标签ID
        
        Returns:
            标签ID列表
        """
        return [t.id for t in self._tabs]
    
    def set_tab_label(self, tab_id: str, label: str):
        """设置标签文本
        
        Args:
            tab_id: 标签ID
            label: 新文本
        """
        tab = self._get_tab(tab_id)
        if not tab:
            return
        
        # 安全处理
        label = html.escape(label[:self.MAX_LABEL_LENGTH])
        tab.label = label
        
        if tab_id in self._tab_buttons:
            btn = self._tab_buttons[tab_id]['label']
            if _CTK_AVAILABLE:
                btn.configure(text=label)
            else:
                btn.configure(text=label)
    
    def destroy(self):
        """销毁组件"""
        self._indicator.destroy()
        
        # 解绑键盘事件
        try:
            self.unbind_all("<Control-Tab>")
            self.unbind_all("<Control-Shift-Tab>")
        except Exception:
            pass
        
        super().destroy()


# 便捷函数
def create_tabs(
    master,
    tabs: List[Dict[str, Any]] = None,
    closable: bool = True,
    draggable: bool = True,
    theme: str = "dark",
    **kwargs
) -> ModernTabs:
    """快速创建标签页组件
    
    Args:
        master: 父容器
        tabs: 初始标签列表 [{"id": "x", "label": "X"}, ...]
        closable: 是否可关闭
        draggable: 是否可拖拽
        theme: 主题
        **kwargs: 其他参数
        
    Returns:
        ModernTabs实例
    """
    tab_widget = ModernTabs(
        master,
        closable=closable,
        draggable=draggable,
        theme=theme,
        **kwargs
    )
    
    if tabs:
        for tab in tabs:
            tab_widget.add_tab(
                tab_id=tab.get("id", str(id(tab))),
                label=tab.get("label", "Tab"),
                closable=tab.get("closable", closable),
                select=tab.get("select", False)
            )
    
    return tab_widget
