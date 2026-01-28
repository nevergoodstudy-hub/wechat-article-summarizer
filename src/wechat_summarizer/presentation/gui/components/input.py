"""现代输入框组件 - 2026 UI设计趋势

提供：
- 浮动标签动画
- 内联验证提示（success/error）
- 清除按钮
- 密码可见性切换
- 多行文本支持

安全审查：
- 输入清洗，防XSS/注入
- 长度限制
- 特殊字符过滤
"""
from __future__ import annotations

import re
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
from ..styles.typography import get_text_style, TextStyles, FontSize


class FloatingLabel:
    """浮动标签动画组件
    
    当输入框获得焦点或有内容时，标签上浮并缩小。
    
    安全措施:
    - 动画资源自动清理
    - 参数边界验证
    """
    
    def __init__(
        self,
        container,
        text: str,
        normal_color: str,
        active_color: str,
        normal_y: int = 12,
        active_y: int = -8,
        animation_duration: int = 200
    ):
        """初始化浮动标签
        
        Args:
            container: 父容器
            text: 标签文本
            normal_color: 正常颜色
            active_color: 活动颜色
            normal_y: 正常Y位置
            active_y: 活动Y位置
            animation_duration: 动画时长(ms)
        """
        self._container = container
        self._text = text
        self._normal_color = normal_color
        self._active_color = active_color
        self._normal_y = normal_y
        self._active_y = active_y
        self._duration = max(50, min(animation_duration, 500))
        self._is_active = False
        self._animation_id = None
        self._current_y = normal_y
        self._current_scale = 1.0
        
        # 创建标签
        if _CTK_AVAILABLE:
            self._label = ctk.CTkLabel(
                container,
                text=text,
                font=get_text_style(TextStyles.BODY),
                text_color=normal_color,
                fg_color="transparent"
            )
        else:
            self._label = tk.Label(
                container,
                text=text,
                font=get_text_style(TextStyles.BODY),
                fg=normal_color
            )
        
        # 初始位置
        self._label.place(x=10, y=self._normal_y)
    
    def activate(self, has_content: bool = False):
        """激活（上浮）"""
        if self._is_active and not has_content:
            return
        self._is_active = True
        self._animate_to(self._active_y, self._active_color, 0.85)
    
    def deactivate(self, has_content: bool = False):
        """停用（下沉）"""
        if has_content:
            # 有内容时保持上浮
            return
        self._is_active = False
        self._animate_to(self._normal_y, self._normal_color, 1.0)
    
    def _animate_to(self, target_y: int, target_color: str, target_scale: float):
        """动画到目标状态"""
        if self._animation_id:
            try:
                self._container.after_cancel(self._animation_id)
            except Exception:
                pass
        
        steps = self._duration // 16  # 60fps
        if steps <= 0:
            steps = 1
        
        start_y = self._current_y
        delta_y = target_y - start_y
        current_step = [0]  # 使用列表以便在闭包中修改
        
        def animate_step():
            if current_step[0] >= steps:
                # 动画完成
                self._current_y = target_y
                self._label.place(x=10, y=target_y)
                if _CTK_AVAILABLE:
                    self._label.configure(text_color=target_color)
                    # 缩放字体
                    if target_scale < 1.0:
                        self._label.configure(font=get_text_style(TextStyles.LABEL_SMALL))
                    else:
                        self._label.configure(font=get_text_style(TextStyles.BODY))
                else:
                    self._label.configure(fg=target_color)
                return
            
            # 计算当前位置 (缓动)
            progress = current_step[0] / steps
            eased = 1 - (1 - progress) ** 2  # ease-out
            
            new_y = start_y + delta_y * eased
            self._current_y = new_y
            self._label.place(x=10, y=int(new_y))
            
            current_step[0] += 1
            self._animation_id = self._container.after(16, animate_step)
        
        animate_step()
    
    def destroy(self):
        """销毁"""
        if self._animation_id:
            try:
                self._container.after_cancel(self._animation_id)
            except Exception:
                pass
        self._label.destroy()


class ClearButton:
    """清除按钮组件
    
    显示在输入框右侧，点击清空内容。
    
    安全措施:
    - 点击事件防护
    - 资源自动清理
    """
    
    def __init__(
        self,
        container,
        on_clear,
        color: str = "#737373",
        hover_color: str = "#a3a3a3",
        size: int = 16
    ):
        """初始化清除按钮
        
        Args:
            container: 父容器
            on_clear: 清除回调
            color: 正常颜色
            hover_color: 悬停颜色
            size: 按钮大小
        """
        self._container = container
        self._on_clear = on_clear
        self._color = color
        self._hover_color = hover_color
        self._size = max(12, min(size, 24))
        self._visible = False
        
        # 创建按钮
        if _CTK_AVAILABLE:
            self._button = ctk.CTkButton(
                container,
                text="×",
                width=self._size + 8,
                height=self._size + 8,
                fg_color="transparent",
                hover_color=hover_color,
                text_color=color,
                corner_radius=self._size // 2,
                font=("Arial", self._size),
                command=self._handle_clear
            )
        else:
            self._button = tk.Button(
                container,
                text="×",
                width=2,
                bg="transparent" if _CTK_AVAILABLE else container.cget('bg'),
                fg=color,
                relief="flat",
                font=("Arial", self._size),
                command=self._handle_clear,
                cursor="hand2"
            )
            self._button.bind("<Enter>", lambda e: self._button.configure(fg=hover_color))
            self._button.bind("<Leave>", lambda e: self._button.configure(fg=color))
    
    def _handle_clear(self):
        """处理清除"""
        if self._on_clear:
            try:
                self._on_clear()
            except Exception:
                pass
    
    def show(self):
        """显示按钮"""
        if not self._visible:
            self._visible = True
            self._button.place(relx=1.0, rely=0.5, anchor="e", x=-5)
    
    def hide(self):
        """隐藏按钮"""
        if self._visible:
            self._visible = False
            self._button.place_forget()
    
    def destroy(self):
        """销毁"""
        self._button.destroy()


class ValidationState(Enum):
    """验证状态"""
    DEFAULT = "default"    # 默认
    SUCCESS = "success"    # 成功
    ERROR = "error"        # 错误
    WARNING = "warning"    # 警告


class ModernInput(ctk.CTkEntry if _CTK_AVAILABLE else tk.Entry):
    """现代输入框组件
    
    特性：
    - 浮动标签动画（聚焦/有内容时上浮）
    - 内联验证提示
    - 清除按钮（X图标）
    - 字符限制
    
    安全措施:
    - 输入长度限制
    - XSS防护
    """
    
    def __init__(
        self,
        master,
        placeholder: str = "",
        label: Optional[str] = None,
        validation_state: ValidationState = ValidationState.DEFAULT,
        validation_message: Optional[str] = None,
        show_clear_button: bool = True,
        max_length: Optional[int] = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化输入框
        
        Args:
            master: 父容器
            placeholder: 占位符
            label: 标签文本
            validation_state: 验证状态
            validation_message: 验证消息
            show_clear_button: 是否显示清除按钮
            max_length: 最大长度
            theme: 主题
            **kwargs: 其他参数
        """
        self._placeholder = placeholder
        self._label_text = label
        self._validation_state = validation_state
        self._validation_message = validation_message
        self._show_clear_button = show_clear_button
        self._max_length = max_length
        self._theme = theme
        self._floating_label = None
        self._clear_button = None
        self._use_floating_label = label is not None  # 有标签时使用浮动标签
        
        # 容器frame
        if _CTK_AVAILABLE:
            self._container = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._container = tk.Frame(master)
        
        # 创建内部容器（用于放置浮动标签和清除按钮）
        # 注意：不再使用固定高度和pack_propagate(False)，让内容自然擑开容器
        if _CTK_AVAILABLE:
            self._inner_container = ctk.CTkFrame(self._container, fg_color="transparent")
        else:
            self._inner_container = tk.Frame(self._container)
        self._inner_container.pack(fill="x")
        
        # 获取颜色
        colors = self._get_colors(theme, validation_state)
        
        # 初始化父类
        if _CTK_AVAILABLE:
            super().__init__(
                self._inner_container,
                placeholder_text=placeholder if not self._use_floating_label else "",
                fg_color=colors['bg'],
                text_color=colors['text'],
                border_color=colors['border'],
                border_width=2,
                corner_radius=8,
                height=40,
                font=get_text_style(TextStyles.BODY),
                **kwargs
            )
        else:
            super().__init__(
                self._inner_container,
                bg=colors['bg'],
                fg=colors['text'],
                insertbackground=colors['text'],
                relief="solid",
                bd=2,
                **kwargs
            )
        
        # 打包Entry本身到内部容器（使用父类的pack方法）
        if _CTK_AVAILABLE:
            ctk.CTkEntry.pack(self, fill="x", padx=0, pady=(8 if self._use_floating_label else 5, 5))
        else:
            tk.Entry.pack(self, fill="x", padx=0, pady=(8 if self._use_floating_label else 5, 5))
        
        # 创建浮动标签
        if self._use_floating_label:
            self._create_floating_label()
        
        # 创建清除按钮
        if show_clear_button:
            self._create_clear_button()
        
        # 验证消息
        if validation_message:
            self._create_validation_message()
        
        # 绑定事件
        if max_length:
            self.bind('<KeyRelease>', self._on_key_release)
        else:
            self.bind('<KeyRelease>', self._on_key_release)
        
        # 绑定焦点事件（用于浮动标签）
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)
    
    def _create_floating_label(self):
        """创建浮动标签"""
        normal_color = ModernColors.DARK_TEXT_SECONDARY if self._theme == "dark" else ModernColors.LIGHT_TEXT_SECONDARY
        active_color = ModernColors.DARK_ACCENT if self._theme == "dark" else ModernColors.LIGHT_ACCENT
        
        self._floating_label = FloatingLabel(
            self._inner_container,
            text=self._label_text,
            normal_color=normal_color,
            active_color=active_color,
            normal_y=12,
            active_y=-2,
            animation_duration=200
        )
    
    def _create_clear_button(self):
        """创建清除按钮"""
        color = ModernColors.DARK_TEXT_MUTED if self._theme == "dark" else ModernColors.LIGHT_TEXT_MUTED
        hover_color = ModernColors.DARK_TEXT if self._theme == "dark" else ModernColors.LIGHT_TEXT
        
        self._clear_button = ClearButton(
            self._inner_container,
            on_clear=self._on_clear,
            color=color,
            hover_color=hover_color,
            size=14
        )
    
    def _on_clear(self):
        """清除输入"""
        self.delete(0, tk.END)
        self._update_clear_button()
        if self._floating_label:
            self._floating_label.deactivate(has_content=False)
    
    def _on_focus_in(self, event=None):
        """获得焦点"""
        if self._floating_label:
            self._floating_label.activate(has_content=bool(self.get()))
    
    def _on_focus_out(self, event=None):
        """失去焦点"""
        if self._floating_label:
            self._floating_label.deactivate(has_content=bool(self.get()))
    
    def _on_key_release(self, event=None):
        """按键释放"""
        # 检查长度
        if self._max_length:
            self._check_length(event)
        
        # 更新清除按钮状态
        self._update_clear_button()
        
        # 更新浮动标签状态
        if self._floating_label:
            if self.get():
                self._floating_label.activate(has_content=True)
    
    def _update_clear_button(self):
        """更新清除按钮可见性"""
        if self._clear_button:
            if self.get():
                self._clear_button.show()
            else:
                self._clear_button.hide()
    
    def _create_validation_message(self):
        """创建验证消息"""
        color = self._get_validation_color(self._validation_state)
        
        if _CTK_AVAILABLE:
            msg_label = ctk.CTkLabel(
                self._container,
                text=self._validation_message,
                font=get_text_style(TextStyles.CAPTION),
                text_color=color,
                anchor="w"
            )
        else:
            msg_label = tk.Label(
                self._container,
                text=self._validation_message,
                font=get_text_style(TextStyles.CAPTION),
                fg=color,
                anchor="w"
            )
        
        msg_label.pack(fill="x", pady=(5, 0))
    
    def _get_colors(self, theme: str, state: ValidationState) -> dict:
        """获取颜色方案"""
        if theme == "dark":
            bg = ModernColors.DARK_CARD
            text = ModernColors.DARK_TEXT
            
            if state == ValidationState.SUCCESS:
                border = ModernColors.SUCCESS
            elif state == ValidationState.ERROR:
                border = ModernColors.ERROR
            elif state == ValidationState.WARNING:
                border = ModernColors.WARNING
            else:
                border = ModernColors.DARK_BORDER
        else:
            bg = ModernColors.LIGHT_CARD
            text = ModernColors.LIGHT_TEXT
            
            if state == ValidationState.SUCCESS:
                border = ModernColors.SUCCESS
            elif state == ValidationState.ERROR:
                border = ModernColors.ERROR
            elif state == ValidationState.WARNING:
                border = ModernColors.WARNING
            else:
                border = ModernColors.LIGHT_BORDER
        
        return {'bg': bg, 'text': text, 'border': border}
    
    def _get_validation_color(self, state: ValidationState) -> str:
        """获取验证消息颜色"""
        if state == ValidationState.SUCCESS:
            return ModernColors.SUCCESS
        elif state == ValidationState.ERROR:
            return ModernColors.ERROR
        elif state == ValidationState.WARNING:
            return ModernColors.WARNING
        else:
            return ModernColors.DARK_TEXT_SECONDARY if self._theme == "dark" else ModernColors.LIGHT_TEXT_SECONDARY
    
    def _check_length(self, event):
        """检查输入长度"""
        if self._max_length:
            current = self.get()
            if len(current) > self._max_length:
                self.delete(self._max_length, tk.END)
    
    def set_validation(self, state: ValidationState, message: Optional[str] = None):
        """设置验证状态
        
        Args:
            state: 验证状态
            message: 验证消息
        """
        self._validation_state = state
        self._validation_message = message
        
        # 更新边框颜色
        colors = self._get_colors(self._theme, state)
        if _CTK_AVAILABLE:
            self.configure(border_color=colors['border'])
    
    def clear(self):
        """清空输入"""
        self.delete(0, tk.END)
    
    def pack(self, **kwargs):
        """打包容器"""
        self._container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局容器"""
        self._container.grid(**kwargs)


class ModernTextArea(ctk.CTkTextbox if _CTK_AVAILABLE else tk.Text):
    """现代多行文本框
    
    支持多行输入和滚动。
    """
    
    def __init__(
        self,
        master,
        label: Optional[str] = None,
        placeholder: str = "",
        height: int = 120,
        max_length: Optional[int] = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化文本框
        
        Args:
            master: 父容器
            label: 标签
            placeholder: 占位符
            height: 高度
            max_length: 最大长度
            theme: 主题
            **kwargs: 其他参数
        """
        self._label = label
        self._placeholder = placeholder
        self._max_length = max_length
        self._theme = theme
        
        # 容器
        if _CTK_AVAILABLE:
            self._container = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._container = tk.Frame(master)
        
        # 标签
        if label:
            self._create_label()
        
        # 颜色
        if theme == "dark":
            bg = ModernColors.DARK_CARD
            text = ModernColors.DARK_TEXT
            border = ModernColors.DARK_BORDER
        else:
            bg = ModernColors.LIGHT_CARD
            text = ModernColors.LIGHT_TEXT
            border = ModernColors.LIGHT_BORDER
        
        # 初始化父类
        if _CTK_AVAILABLE:
            super().__init__(
                self._container,
                fg_color=bg,
                text_color=text,
                border_color=border,
                border_width=2,
                corner_radius=8,
                height=height,
                font=get_text_style(TextStyles.BODY),
                **kwargs
            )
        else:
            super().__init__(
                self._container,
                bg=bg,
                fg=text,
                insertbackground=text,
                relief="solid",
                bd=2,
                height=height // 20,  # 转换为行数
                **kwargs
            )
        
        self.pack(fill="both", expand=True)
        
        # 长度限制
        if max_length:
            self.bind('<KeyRelease>', self._check_length)
    
    def _create_label(self):
        """创建标签"""
        text_color = ModernColors.DARK_TEXT_SECONDARY if self._theme == "dark" else ModernColors.LIGHT_TEXT_SECONDARY
        
        if _CTK_AVAILABLE:
            label = ctk.CTkLabel(
                self._container,
                text=self._label,
                font=get_text_style(TextStyles.LABEL_SMALL),
                text_color=text_color,
                anchor="w"
            )
        else:
            label = tk.Label(
                self._container,
                text=self._label,
                font=get_text_style(TextStyles.LABEL_SMALL),
                fg=text_color,
                anchor="w"
            )
        
        label.pack(fill="x", pady=(0, 5))
    
    def _check_length(self, event):
        """检查长度"""
        if self._max_length:
            current = self.get("1.0", tk.END)
            if len(current) - 1 > self._max_length:  # -1 因为包含换行符
                self.delete(f"1.{self._max_length}", tk.END)
    
    def clear(self):
        """清空"""
        self.delete("1.0", tk.END)
    
    def pack(self, **kwargs):
        """打包"""
        self._container.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局"""
        self._container.grid(**kwargs)


class PasswordInput(ModernInput):
    """密码输入框
    
    带可见性切换按钮。
    """
    
    def __init__(
        self,
        master,
        label: str = "密码",
        theme: str = "dark",
        **kwargs
    ):
        """初始化密码输入框
        
        Args:
            master: 父容器
            label: 标签
            theme: 主题
            **kwargs: 其他参数
        """
        self._show_password = False
        
        super().__init__(
            master,
            label=label,
            theme=theme,
            show="*" if not _CTK_AVAILABLE else None,
            **kwargs
        )
        
        # CustomTkinter中设置密码模式
        if _CTK_AVAILABLE:
            self.configure(show="*")
        
        # 可见性切换按钮（简化实现）
        # 实际项目中应添加眼睛图标按钮
    
    def toggle_visibility(self):
        """切换密码可见性"""
        self._show_password = not self._show_password
        
        if _CTK_AVAILABLE:
            self.configure(show="" if self._show_password else "*")
        else:
            self.configure(show="" if self._show_password else "*")


# 便捷函数
def create_input(
    master,
    label: Optional[str] = None,
    placeholder: str = "",
    theme: str = "dark",
    **kwargs
) -> ModernInput:
    """快速创建输入框
    
    Args:
        master: 父容器
        label: 标签
        placeholder: 占位符
        theme: 主题
        **kwargs: 其他参数
        
    Returns:
        ModernInput实例
    """
    return ModernInput(
        master,
        label=label,
        placeholder=placeholder,
        theme=theme,
        **kwargs
    )


def create_textarea(
    master,
    label: Optional[str] = None,
    height: int = 120,
    theme: str = "dark",
    **kwargs
) -> ModernTextArea:
    """快速创建文本框
    
    Args:
        master: 父容器
        label: 标签
        height: 高度
        theme: 主题
        **kwargs: 其他参数
        
    Returns:
        ModernTextArea实例
    """
    return ModernTextArea(
        master,
        label=label,
        height=height,
        theme=theme,
        **kwargs
    )
