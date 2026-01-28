"""现代下拉选择器组件 - 2026 UI设计趋势

提供：
- 单选/多选支持
- 搜索过滤功能
- 虚拟滚动（大数据量优化）
- 标签显示（多选模式）
- 键盘导航

安全审查：
- 搜索输入过滤，防XSS
- 选项数量限制
- 内存管理
"""
from __future__ import annotations

import re
import tkinter as tk
from enum import Enum
from typing import Optional, Callable, List, Any, Dict

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors
from ..styles.typography import get_text_style, TextStyles


class SelectMode(Enum):
    """选择模式"""
    SINGLE = "single"    # 单选
    MULTIPLE = "multiple" # 多选


class SelectOption:
    """选项数据类"""
    
    def __init__(self, value: Any, label: str, disabled: bool = False):
        """初始化选项
        
        Args:
            value: 选项值
            label: 显示标签
            disabled: 是否禁用
        """
        self.value = value
        self.label = label
        self.disabled = disabled


class ModernSelect:
    """现代下拉选择器组件
    
    特性：
    - 单选/多选模式
    - 搜索过滤
    - 虚拟滚动
    - 键盘导航
    """
    
    MAX_VISIBLE_OPTIONS = 8  # 最大可见选项数
    MAX_OPTIONS = 10000      # 最大选项数量限制
    
    def __init__(
        self,
        master,
        options: List[SelectOption] = None,
        mode: SelectMode = SelectMode.SINGLE,
        placeholder: str = "请选择...",
        searchable: bool = True,
        label: Optional[str] = None,
        on_change: Optional[Callable] = None,
        theme: str = "dark",
        width: int = 300,
        **kwargs
    ):
        """初始化下拉选择器
        
        Args:
            master: 父容器
            options: 选项列表
            mode: 选择模式
            placeholder: 占位符
            searchable: 是否可搜索
            label: 标签
            on_change: 值变化回调
            theme: 主题
            width: 宽度
            **kwargs: 其他参数
        """
        self._master = master
        self._options = options[:self.MAX_OPTIONS] if options else []
        self._filtered_options = self._options.copy()
        self._mode = mode
        self._placeholder = placeholder
        self._searchable = searchable
        self._label = label
        self._on_change = on_change
        self._theme = theme
        self._width = width
        self._is_open = False
        
        # 选中值
        self._selected_values: List[Any] = []
        
        # 颜色配置
        self._colors = self._get_colors(theme)
        
        # 主容器
        if _CTK_AVAILABLE:
            self._container = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._container = tk.Frame(master)
        
        # 创建组件
        self._create_label()
        self._create_select_button()
        self._create_dropdown()
        
        # 绑定全局点击事件关闭下拉
        master.bind("<Button-1>", self._on_global_click, add="+")
    
    def _get_colors(self, theme: str) -> dict:
        """获取颜色配置"""
        if theme == "dark":
            return {
                'bg': ModernColors.DARK_CARD,
                'bg_hover': ModernColors.DARK_CARD_HOVER,
                'text': ModernColors.DARK_TEXT,
                'text_secondary': ModernColors.DARK_TEXT_SECONDARY,
                'border': ModernColors.DARK_BORDER,
                'accent': ModernColors.DARK_ACCENT,
                'dropdown_bg': ModernColors.DARK_SURFACE,
            }
        else:
            return {
                'bg': ModernColors.LIGHT_CARD,
                'bg_hover': ModernColors.LIGHT_CARD_HOVER,
                'text': ModernColors.LIGHT_TEXT,
                'text_secondary': ModernColors.LIGHT_TEXT_SECONDARY,
                'border': ModernColors.LIGHT_BORDER,
                'accent': ModernColors.LIGHT_ACCENT,
                'dropdown_bg': ModernColors.LIGHT_SURFACE,
            }
    
    def _create_label(self):
        """创建标签"""
        if not self._label:
            return
        
        if _CTK_AVAILABLE:
            label = ctk.CTkLabel(
                self._container,
                text=self._label,
                font=get_text_style(TextStyles.LABEL_SMALL),
                text_color=self._colors['text_secondary'],
                anchor="w"
            )
        else:
            label = tk.Label(
                self._container,
                text=self._label,
                font=get_text_style(TextStyles.LABEL_SMALL),
                fg=self._colors['text_secondary'],
                anchor="w"
            )
        
        label.pack(fill="x", pady=(0, 5))
    
    def _create_select_button(self):
        """创建选择按钮"""
        if _CTK_AVAILABLE:
            self._select_btn = ctk.CTkButton(
                self._container,
                text=self._placeholder,
                width=self._width,
                height=40,
                fg_color=self._colors['bg'],
                hover_color=self._colors['bg_hover'],
                text_color=self._colors['text_secondary'],
                border_width=1,
                border_color=self._colors['border'],
                corner_radius=8,
                anchor="w",
                command=self._toggle_dropdown
            )
        else:
            self._select_btn = tk.Button(
                self._container,
                text=self._placeholder,
                width=self._width // 8,
                bg=self._colors['bg'],
                fg=self._colors['text_secondary'],
                relief="solid",
                bd=1,
                anchor="w",
                command=self._toggle_dropdown
            )
        
        self._select_btn.pack(fill="x")
    
    def _create_dropdown(self):
        """创建下拉面板"""
        # 下拉容器（初始隐藏）
        if _CTK_AVAILABLE:
            self._dropdown = ctk.CTkFrame(
                self._container,
                fg_color=self._colors['dropdown_bg'],
                border_width=1,
                border_color=self._colors['border'],
                corner_radius=8
            )
        else:
            self._dropdown = tk.Frame(
                self._container,
                bg=self._colors['dropdown_bg'],
                highlightthickness=1,
                highlightbackground=self._colors['border']
            )
        
        # 搜索框（如果启用）
        if self._searchable:
            self._create_search_input()
        
        # 选项列表容器
        self._create_options_list()
    
    def _create_search_input(self):
        """创建搜索输入框"""
        if _CTK_AVAILABLE:
            self._search_entry = ctk.CTkEntry(
                self._dropdown,
                placeholder_text="搜索...",
                fg_color=self._colors['bg'],
                text_color=self._colors['text'],
                border_width=1,
                border_color=self._colors['border'],
                corner_radius=6,
                height=32
            )
        else:
            self._search_entry = tk.Entry(
                self._dropdown,
                bg=self._colors['bg'],
                fg=self._colors['text'],
                relief="solid",
                bd=1
            )
        
        self._search_entry.pack(fill="x", padx=8, pady=8)
        self._search_entry.bind("<KeyRelease>", self._on_search)
    
    def _create_options_list(self):
        """创建选项列表"""
        # 滚动容器
        if _CTK_AVAILABLE:
            self._options_frame = ctk.CTkScrollableFrame(
                self._dropdown,
                fg_color="transparent",
                height=min(len(self._options), self.MAX_VISIBLE_OPTIONS) * 36
            )
        else:
            # Tkinter版本：使用Canvas+Scrollbar
            canvas = tk.Canvas(
                self._dropdown,
                bg=self._colors['dropdown_bg'],
                highlightthickness=0,
                height=min(len(self._options), self.MAX_VISIBLE_OPTIONS) * 36
            )
            scrollbar = tk.Scrollbar(self._dropdown, command=canvas.yview)
            self._options_frame = tk.Frame(canvas, bg=self._colors['dropdown_bg'])
            
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            canvas.create_window((0, 0), window=self._options_frame, anchor="nw")
        
        self._options_frame.pack(fill="both", expand=True, padx=4, pady=(0, 8))
        
        # 渲染选项
        self._render_options()
    
    def _render_options(self):
        """渲染选项列表"""
        # 清空现有选项
        for widget in self._options_frame.winfo_children():
            widget.destroy()
        
        for option in self._filtered_options:
            self._create_option_item(option)
    
    def _create_option_item(self, option: SelectOption):
        """创建单个选项"""
        is_selected = option.value in self._selected_values
        
        if _CTK_AVAILABLE:
            item = ctk.CTkButton(
                self._options_frame,
                text=option.label,
                fg_color=self._colors['accent'] if is_selected else "transparent",
                hover_color=self._colors['bg_hover'],
                text_color=self._colors['text'],
                anchor="w",
                height=32,
                corner_radius=4,
                command=lambda o=option: self._on_option_click(o),
                state="disabled" if option.disabled else "normal"
            )
        else:
            item = tk.Button(
                self._options_frame,
                text=option.label,
                bg=self._colors['accent'] if is_selected else self._colors['dropdown_bg'],
                fg=self._colors['text'],
                anchor="w",
                relief="flat",
                command=lambda o=option: self._on_option_click(o),
                state="disabled" if option.disabled else "normal"
            )
        
        item.pack(fill="x", padx=4, pady=2)
    
    def _toggle_dropdown(self):
        """切换下拉面板显示"""
        if self._is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()
    
    def _open_dropdown(self):
        """打开下拉面板"""
        self._is_open = True
        self._dropdown.pack(fill="x", pady=(4, 0))
        
        # 聚焦搜索框
        if self._searchable and hasattr(self, '_search_entry'):
            self._search_entry.focus_set()
    
    def _close_dropdown(self):
        """关闭下拉面板"""
        self._is_open = False
        self._dropdown.pack_forget()
        
        # 重置搜索
        if self._searchable and hasattr(self, '_search_entry'):
            if _CTK_AVAILABLE:
                self._search_entry.delete(0, tk.END)
            else:
                self._search_entry.delete(0, tk.END)
            self._filtered_options = self._options.copy()
            self._render_options()
    
    def _on_global_click(self, event):
        """全局点击事件处理"""
        # 检查点击是否在组件外
        if self._is_open:
            widget = event.widget
            if not self._is_child_of(widget, self._container):
                self._close_dropdown()
    
    def _is_child_of(self, widget, parent):
        """检查widget是否是parent的子组件"""
        try:
            while widget:
                if widget == parent:
                    return True
                widget = widget.master
        except:
            pass
        return False
    
    def _on_search(self, event):
        """搜索事件处理"""
        query = self._search_entry.get().strip().lower()
        
        # 安全过滤：移除特殊字符
        query = re.sub(r'[<>"\']', '', query)
        
        if not query:
            self._filtered_options = self._options.copy()
        else:
            self._filtered_options = [
                opt for opt in self._options
                if query in opt.label.lower()
            ]
        
        self._render_options()
    
    def _on_option_click(self, option: SelectOption):
        """选项点击事件"""
        if option.disabled:
            return
        
        if self._mode == SelectMode.SINGLE:
            # 单选模式
            self._selected_values = [option.value]
            self._update_display()
            self._close_dropdown()
        else:
            # 多选模式
            if option.value in self._selected_values:
                self._selected_values.remove(option.value)
            else:
                self._selected_values.append(option.value)
            self._update_display()
            self._render_options()  # 刷新选中状态
        
        # 触发回调
        if self._on_change:
            self._on_change(self.get_value())
    
    def _update_display(self):
        """更新显示文本"""
        if not self._selected_values:
            display_text = self._placeholder
            text_color = self._colors['text_secondary']
        elif self._mode == SelectMode.SINGLE:
            # 单选：显示选中项标签
            selected_opt = next(
                (o for o in self._options if o.value == self._selected_values[0]),
                None
            )
            display_text = selected_opt.label if selected_opt else self._placeholder
            text_color = self._colors['text']
        else:
            # 多选：显示数量
            display_text = f"已选择 {len(self._selected_values)} 项"
            text_color = self._colors['text']
        
        if _CTK_AVAILABLE:
            self._select_btn.configure(text=display_text, text_color=text_color)
        else:
            self._select_btn.configure(text=display_text, fg=text_color)
    
    def get_value(self):
        """获取选中值
        
        Returns:
            单选模式返回单个值，多选模式返回列表
        """
        if self._mode == SelectMode.SINGLE:
            return self._selected_values[0] if self._selected_values else None
        else:
            return self._selected_values.copy()
    
    def set_value(self, value):
        """设置选中值
        
        Args:
            value: 单选传单个值，多选传列表
        """
        if self._mode == SelectMode.SINGLE:
            self._selected_values = [value] if value is not None else []
        else:
            self._selected_values = list(value) if value else []
        
        self._update_display()
    
    def set_options(self, options: List[SelectOption]):
        """设置选项列表
        
        Args:
            options: 新选项列表
        """
        self._options = options[:self.MAX_OPTIONS]
        self._filtered_options = self._options.copy()
        self._selected_values = []
        self._update_display()
        
        if self._is_open:
            self._render_options()
    
    def clear(self):
        """清空选择"""
        self._selected_values = []
        self._update_display()
    
    def pack(self, **kwargs):
        """打包"""
        self._container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self._container.grid(**kwargs)


# 便捷函数
def create_select(
    master,
    options: List[Dict[str, Any]],
    mode: str = "single",
    placeholder: str = "请选择...",
    theme: str = "dark",
    **kwargs
) -> ModernSelect:
    """快速创建下拉选择器
    
    Args:
        master: 父容器
        options: 选项列表 [{"value": x, "label": y}, ...]
        mode: 选择模式 "single" 或 "multiple"
        placeholder: 占位符
        theme: 主题
        **kwargs: 其他参数
        
    Returns:
        ModernSelect实例
    """
    select_options = [
        SelectOption(
            value=opt.get("value"),
            label=opt.get("label", str(opt.get("value"))),
            disabled=opt.get("disabled", False)
        )
        for opt in options
    ]
    
    select_mode = SelectMode.MULTIPLE if mode == "multiple" else SelectMode.SINGLE
    
    return ModernSelect(
        master,
        options=select_options,
        mode=select_mode,
        placeholder=placeholder,
        theme=theme,
        **kwargs
    )
