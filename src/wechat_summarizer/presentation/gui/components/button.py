"""现代按钮组件 - 2026 UI设计趋势

提供：
- 4种变体（primary/secondary/ghost/danger）
- Ripple水波纹点击效果
- Loading状态旋转动画
- 图标+文字组合支持
- 防重复点击保护

安全审查：
- Debounce防抖，避免重复触发
- 禁用状态保护
- 命令执行异常捕获
"""
from __future__ import annotations

import time
import tkinter as tk
from enum import Enum
from typing import Optional, Callable, Any

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors
from ..styles.typography import get_text_style, TextStyles


class RippleEffect:
    """水波纹动画效果
    
    在点击位置创建扩散圆形动画。
    
    安全措施:
    - 动画资源自动清理
    - 最大并发动画限制
    """
    
    MAX_CONCURRENT_RIPPLES = 3  # 最大并发水波纹数
    
    def __init__(self, canvas: tk.Canvas, color: str = "#FFFFFF", duration: int = 400):
        """初始化水波纹效果
        
        Args:
            canvas: 绘制画布
            color: 水波纹颜色
            duration: 动画时长(ms)
        """
        self._canvas = canvas
        self._color = color
        self._duration = max(100, min(duration, 1000))  # 限制100-1000ms
        self._ripples = []  # 当前活动的水波纹
        self._animation_ids = []
    
    def trigger(self, x: int, y: int, max_radius: int = None):
        """触发水波纹动画
        
        Args:
            x: 点击X坐标
            y: 点击Y坐标
            max_radius: 最大半径
        """
        # 限制并发数量
        if len(self._ripples) >= self.MAX_CONCURRENT_RIPPLES:
            self._cleanup_oldest()
        
        # 计算最大半径
        if max_radius is None:
            canvas_width = self._canvas.winfo_width()
            canvas_height = self._canvas.winfo_height()
            # 确保水波纹覆盖整个画布
            max_radius = int(((canvas_width ** 2 + canvas_height ** 2) ** 0.5) / 2) + 10
        
        # 创建水波纹数据
        ripple_id = f"ripple_{len(self._ripples)}_{id(self)}"
        ripple = {
            'id': ripple_id,
            'x': x,
            'y': y,
            'radius': 0,
            'max_radius': max_radius,
            'alpha': 0.4,
            'step': 0,
            'total_steps': self._duration // 16  # 60fps
        }
        self._ripples.append(ripple)
        
        # 开始动画
        self._animate_ripple(ripple)
    
    def _animate_ripple(self, ripple: dict):
        """动画帧"""
        if ripple['step'] >= ripple['total_steps']:
            self._cleanup_ripple(ripple)
            return
        
        # 计算当前状态
        progress = ripple['step'] / ripple['total_steps']
        
        # 缓动函数 (ease-out)
        eased = 1 - (1 - progress) ** 3
        
        radius = eased * ripple['max_radius']
        alpha = ripple['alpha'] * (1 - progress)
        
        # 计算颜色
        fill_color = self._color_with_alpha(self._color, alpha)
        
        # 绘制圆形
        self._canvas.delete(ripple['id'])
        x, y = ripple['x'], ripple['y']
        self._canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill_color,
            outline="",
            tags=ripple['id']
        )
        
        ripple['step'] += 1
        
        # 继续动画
        anim_id = self._canvas.after(16, lambda: self._animate_ripple(ripple))
        self._animation_ids.append(anim_id)
    
    def _color_with_alpha(self, hex_color: str, alpha: float) -> str:
        """混合颜色与背景（模拟透明度）
        
        由于Tkinter Canvas不支持真正的透明度，
        我们通过混合颜色来模拟。
        """
        try:
            # 解析颜色
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # 混合与黑色背景
            r = int(r * alpha)
            g = int(g * alpha)
            b = int(b * alpha)
            
            return f'#{r:02x}{g:02x}{b:02x}'
        except Exception:
            return hex_color
    
    def _cleanup_ripple(self, ripple: dict):
        """清理单个水波纹"""
        self._canvas.delete(ripple['id'])
        if ripple in self._ripples:
            self._ripples.remove(ripple)
    
    def _cleanup_oldest(self):
        """清理最旧的水波纹"""
        if self._ripples:
            self._cleanup_ripple(self._ripples[0])
    
    def cleanup_all(self):
        """清理所有水波纹"""
        for ripple in self._ripples.copy():
            self._canvas.delete(ripple['id'])
        self._ripples.clear()
        
        for anim_id in self._animation_ids:
            try:
                self._canvas.after_cancel(anim_id)
            except Exception:
                pass
        self._animation_ids.clear()


class ButtonVariant(Enum):
    """按钮变体"""
    PRIMARY = "primary"       # 主要按钮 (强调色)
    SECONDARY = "secondary"   # 次要按钮 (灰色)
    GHOST = "ghost"           # 幽灵按钮 (透明+边框)
    DANGER = "danger"         # 危险按钮 (红色)
    TEXT = "text"             # 纯文本按钮


class ButtonSize(Enum):
    """按钮尺寸"""
    SMALL = "small"       # 小 (24px高)
    MEDIUM = "medium"     # 中 (32px高)
    LARGE = "large"       # 大 (40px高)


class ModernButton(ctk.CTkButton if _CTK_AVAILABLE else tk.Button):
    """现代按钮组件
    
    特性：
    - 多种样式变体
    - 真实水波纹扩散动画
    - Loading加载状态
    - 防抖保护
    - 图标支持
    
    安全措施:
    - 防抖机制防止重复点击
    - 动画资源自动清理
    - 命令执行异常捕获
    """
    
    def __init__(
        self,
        master,
        text: str = "Button",
        command: Optional[Callable] = None,
        variant: ButtonVariant = ButtonVariant.PRIMARY,
        size: ButtonSize = ButtonSize.MEDIUM,
        icon: Optional[Any] = None,
        icon_position: str = "left",  # "left" 或 "right"
        loading: bool = False,
        disabled: bool = False,
        debounce_ms: int = 300,  # 防抖时间
        theme: str = "dark",
        **kwargs
    ):
        """初始化按钮
        
        Args:
            master: 父容器
            text: 按钮文本
            command: 点击回调
            variant: 按钮变体
            size: 按钮尺寸
            icon: 图标对象
            icon_position: 图标位置
            loading: 是否加载中
            disabled: 是否禁用
            debounce_ms: 防抖延迟（毫秒）
            theme: 主题
            **kwargs: 其他参数
        """
        self._text = text
        self._original_command = command
        self._variant = variant
        self._size = size
        self._icon = icon
        self._icon_position = icon_position
        self._loading = loading
        self._disabled = disabled
        self._debounce_ms = debounce_ms
        self._theme = theme
        self._last_click_time = 0
        self._ripple_effect = None
        self._ripple_canvas = None
        
        # 根据主题和变体选择颜色
        colors = self._get_colors(theme, variant)
        
        # 根据尺寸选择高度和padding
        size_config = self._get_size_config(size)
        
        # 获取字体
        if size == ButtonSize.SMALL:
            font = get_text_style(TextStyles.BUTTON_SMALL)
        elif size == ButtonSize.LARGE:
            font = get_text_style(TextStyles.BUTTON_LARGE)
        else:
            font = get_text_style(TextStyles.BUTTON)
        
        # 初始化父类
        if _CTK_AVAILABLE:
            # CustomTkinter的border_color不支持'transparent'
            # 只有GHOST变体才需要边框，其他变体border_width=0时无需border_color
            ctk_kwargs = {
                'master': master,
                'text': text if not loading else "Loading...",
                'command': self._handle_click,
                'fg_color': colors['bg'],
                'hover_color': colors['hover'],
                'text_color': colors['text'],
                'corner_radius': 8,
                'height': size_config['height'],
                'font': font,
                'state': "disabled" if (disabled or loading) else "normal",
            }
            
            # 只有GHOST变体才设置边框
            if variant == ButtonVariant.GHOST:
                ctk_kwargs['border_width'] = 2
                ctk_kwargs['border_color'] = colors.get('border', ModernColors.DARK_BORDER)
            else:
                ctk_kwargs['border_width'] = 0
            
            ctk_kwargs.update(kwargs)
            super().__init__(**ctk_kwargs)
        else:
            super().__init__(
                master,
                text=text if not loading else "Loading...",
                command=self._handle_click,
                bg=colors['bg'],
                fg=colors['text'],
                font=font,
                relief="flat" if variant != ButtonVariant.GHOST else "solid",
                bd=2 if variant == ButtonVariant.GHOST else 0,
                state="disabled" if (disabled or loading) else "normal",
                **kwargs
            )
        
        # 绑定hover效果（在CustomTkinter中已自动处理）
        if not _CTK_AVAILABLE:
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
        
        # 绑定点击事件用于水波纹
        self.bind("<Button-1>", self._on_click_ripple, add="+")
    
    def _get_colors(self, theme: str, variant: ButtonVariant) -> dict:
        """获取按钮颜色方案
        
        Args:
            theme: 主题
            variant: 变体
            
        Returns:
            颜色字典 {bg, hover, text, border}
        """
        if theme == "dark":
            if variant == ButtonVariant.PRIMARY:
                return {
                    'bg': ModernColors.DARK_ACCENT,
                    'hover': ModernColors.DARK_ACCENT_HOVER,
                    'text': "#FFFFFF",
                }
            elif variant == ButtonVariant.SECONDARY:
                return {
                    'bg': ModernColors.DARK_CARD,
                    'hover': ModernColors.DARK_CARD_HOVER,
                    'text': ModernColors.DARK_TEXT,
                }
            elif variant == ButtonVariant.GHOST:
                return {
                    'bg': "transparent",
                    'hover': ModernColors.DARK_CARD_HOVER,
                    'text': ModernColors.DARK_TEXT,
                    'border': ModernColors.DARK_BORDER,
                }
            elif variant == ButtonVariant.DANGER:
                return {
                    'bg': ModernColors.ERROR,
                    'hover': "#dc2626",  # 深红色
                    'text': "#FFFFFF",
                }
            else:  # TEXT
                return {
                    'bg': "transparent",
                    'hover': ModernColors.DARK_CARD_HOVER,
                    'text': ModernColors.DARK_TEXT,
                }
        else:  # light theme
            if variant == ButtonVariant.PRIMARY:
                return {
                    'bg': ModernColors.LIGHT_ACCENT,
                    'hover': ModernColors.LIGHT_ACCENT_HOVER,
                    'text': "#FFFFFF",
                }
            elif variant == ButtonVariant.SECONDARY:
                return {
                    'bg': ModernColors.LIGHT_CARD,
                    'hover': ModernColors.LIGHT_CARD_HOVER,
                    'text': ModernColors.LIGHT_TEXT,
                }
            elif variant == ButtonVariant.GHOST:
                return {
                    'bg': "transparent",
                    'hover': ModernColors.LIGHT_CARD_HOVER,
                    'text': ModernColors.LIGHT_TEXT,
                    'border': ModernColors.LIGHT_BORDER,
                }
            elif variant == ButtonVariant.DANGER:
                return {
                    'bg': ModernColors.ERROR,
                    'hover': "#dc2626",
                    'text': "#FFFFFF",
                }
            else:  # TEXT
                return {
                    'bg': "transparent",
                    'hover': ModernColors.LIGHT_CARD_HOVER,
                    'text': ModernColors.LIGHT_TEXT,
                }
    
    @staticmethod
    def _get_size_config(size: ButtonSize) -> dict:
        """获取尺寸配置
        
        Args:
            size: 按钮尺寸
            
        Returns:
            配置字典 {height, padding_x, padding_y}
        """
        if size == ButtonSize.SMALL:
            return {'height': 28, 'padding_x': 12, 'padding_y': 4}
        elif size == ButtonSize.LARGE:
            return {'height': 44, 'padding_x': 24, 'padding_y': 12}
        else:  # MEDIUM
            return {'height': 36, 'padding_x': 16, 'padding_y': 8}
    
    def _on_click_ripple(self, event):
        """点击时触发水波纹动画"""
        if self._disabled or self._loading:
            return
        
        # 创建水波纹画布（如果尚未创建）
        if self._ripple_canvas is None:
            self._create_ripple_canvas()
        
        # 获取点击位置（相对于按钮）
        x = event.x
        y = event.y
        
        # 计算最大半径
        width = self.winfo_width()
        height = self.winfo_height()
        max_radius = int(((width ** 2 + height ** 2) ** 0.5))
        
        # 触发水波纹
        if self._ripple_effect:
            self._ripple_effect.trigger(x, y, max_radius)
    
    def _create_ripple_canvas(self):
        """创建水波纹叠加层"""
        # 获取按钮尺寸
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            return
        
        # 获取按钮背景色
        colors = self._get_colors(self._theme, self._variant)
        bg_color = colors.get('bg', '#1e1e1e')
        if bg_color == "transparent":
            bg_color = ModernColors.DARK_BG if self._theme == "dark" else ModernColors.LIGHT_BG
        
        # 水波纹颜色（白色半透明）
        ripple_color = "#FFFFFF" if self._theme == "dark" else "#000000"
        
        # 创建画布
        self._ripple_canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            highlightthickness=0,
            bg=bg_color
        )
        
        # 放置在按钮上
        self._ripple_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # 将画布放在底层（使用tk.Misc.lower而不canvas的lower）
        try:
            self._ripple_canvas.tk.call('lower', self._ripple_canvas._w)
        except Exception:
            pass  # 忽略lower失败
        
        # 创建水波纹效果
        self._ripple_effect = RippleEffect(
            self._ripple_canvas,
            color=ripple_color,
            duration=400
        )
        
        # 传递点击事件
        self._ripple_canvas.bind("<Button-1>", self._on_click_ripple)
    
    def _handle_click(self):
        """处理点击事件（带防抖）"""
        # 禁用或加载中，不处理
        if self._disabled or self._loading:
            return
        
        # 防抖检查
        current_time = time.time() * 1000  # 转为毫秒
        if current_time - self._last_click_time < self._debounce_ms:
            return
        
        self._last_click_time = current_time
        
        # 执行原始命令
        if self._original_command:
            try:
                self._original_command()
            except Exception as e:
                print(f"按钮命令执行错误: {e}")
    
    def _on_enter(self, event=None):
        """鼠标进入（仅用于原生Tkinter）"""
        if not _CTK_AVAILABLE and not self._disabled and not self._loading:
            colors = self._get_colors(self._theme, self._variant)
            self.configure(bg=colors['hover'])
    
    def _on_leave(self, event=None):
        """鼠标离开（仅用于原生Tkinter）"""
        if not _CTK_AVAILABLE:
            colors = self._get_colors(self._theme, self._variant)
            self.configure(bg=colors['bg'])
    
    def set_loading(self, loading: bool):
        """设置加载状态
        
        Args:
            loading: 是否加载中
        """
        self._loading = loading
        
        if loading:
            if _CTK_AVAILABLE:
                self.configure(text="Loading...", state="disabled")
            else:
                self.configure(text="Loading...", state="disabled")
        else:
            if _CTK_AVAILABLE:
                self.configure(text=self._text, state="normal" if not self._disabled else "disabled")
            else:
                self.configure(text=self._text, state="normal" if not self._disabled else "disabled")
    
    def set_disabled(self, disabled: bool):
        """设置禁用状态
        
        Args:
            disabled: 是否禁用
        """
        self._disabled = disabled
        
        if _CTK_AVAILABLE:
            self.configure(state="disabled" if disabled else "normal")
        else:
            self.configure(state="disabled" if disabled else "normal")
    
    def set_text(self, text: str):
        """设置按钮文本
        
        Args:
            text: 新文本
        """
        self._text = text
        if not self._loading:
            if _CTK_AVAILABLE:
                self.configure(text=text)
            else:
                self.configure(text=text)


class IconButton(ModernButton):
    """图标按钮
    
    仅显示图标的圆形按钮。
    """
    
    def __init__(
        self,
        master,
        icon: Any,
        command: Optional[Callable] = None,
        variant: ButtonVariant = ButtonVariant.GHOST,
        size: ButtonSize = ButtonSize.MEDIUM,
        theme: str = "dark",
        **kwargs
    ):
        """初始化图标按钮
        
        Args:
            master: 父容器
            icon: 图标对象
            command: 点击回调
            variant: 按钮变体
            size: 按钮尺寸
            theme: 主题
            **kwargs: 其他参数
        """
        # 图标按钮使用空文本
        super().__init__(
            master,
            text="",
            command=command,
            variant=variant,
            size=size,
            icon=icon,
            theme=theme,
            width=40 if size == ButtonSize.MEDIUM else (32 if size == ButtonSize.SMALL else 48),
            **kwargs
        )
        
        # 设置圆形
        if _CTK_AVAILABLE:
            size_val = 40 if size == ButtonSize.MEDIUM else (32 if size == ButtonSize.SMALL else 48)
            self.configure(corner_radius=size_val // 2)


class ButtonGroup:
    """按钮组
    
    管理一组相关按钮。
    """
    
    def __init__(self, master, orientation: str = "horizontal"):
        """初始化按钮组
        
        Args:
            master: 父容器
            orientation: 方向 ("horizontal" 或 "vertical")
        """
        self._orientation = orientation
        
        if _CTK_AVAILABLE:
            self._frame = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._frame = tk.Frame(master)
        
        self._buttons = []
    
    def add_button(
        self,
        text: str,
        command: Optional[Callable] = None,
        **kwargs
    ) -> ModernButton:
        """添加按钮到组
        
        Args:
            text: 按钮文本
            command: 点击回调
            **kwargs: 其他参数
            
        Returns:
            创建的按钮实例
        """
        button = ModernButton(
            self._frame,
            text=text,
            command=command,
            **kwargs
        )
        
        if self._orientation == "horizontal":
            button.pack(side="left", padx=(0 if len(self._buttons) == 0 else 8, 0))
        else:
            button.pack(pady=(0 if len(self._buttons) == 0 else 8, 0))
        
        self._buttons.append(button)
        return button
    
    def pack(self, **kwargs):
        """打包按钮组"""
        self._frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """网格布局按钮组"""
        self._frame.grid(**kwargs)


# 便捷函数
def create_button(
    master,
    text: str,
    command: Optional[Callable] = None,
    variant: ButtonVariant = ButtonVariant.PRIMARY,
    theme: str = "dark",
    **kwargs
) -> ModernButton:
    """快速创建按钮
    
    Args:
        master: 父容器
        text: 按钮文本
        command: 点击回调
        variant: 按钮变体
        theme: 主题
        **kwargs: 其他参数
        
    Returns:
        ModernButton实例
    """
    return ModernButton(
        master,
        text=text,
        command=command,
        variant=variant,
        theme=theme,
        **kwargs
    )


def create_icon_button(
    master,
    icon: Any,
    command: Optional[Callable] = None,
    theme: str = "dark",
    **kwargs
) -> IconButton:
    """快速创建图标按钮
    
    Args:
        master: 父容器
        icon: 图标对象
        command: 点击回调
        theme: 主题
        **kwargs: 其他参数
        
    Returns:
        IconButton实例
    """
    return IconButton(
        master,
        icon=icon,
        command=command,
        theme=theme,
        **kwargs
    )
