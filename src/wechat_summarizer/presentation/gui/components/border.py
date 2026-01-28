"""现代边框和分隔线组件 - 2026 UI设计趋势

提供：
- 渐变色边框
- 发光边框效果
- 动画边框
- 分隔线组件

安全审查：
- 颜色值验证
- 动画资源管理
- 内存泄漏防护
"""
from __future__ import annotations

import tkinter as tk
import math
from enum import Enum
from typing import Optional, Tuple, List, Union
import re

try:
    import customtkinter as ctk
    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None

from ..styles.colors import ModernColors, to_tkinter_color


class GradientDirection(Enum):
    """渐变方向"""
    HORIZONTAL = "horizontal"    # 水平
    VERTICAL = "vertical"        # 垂直
    DIAGONAL = "diagonal"        # 对角线
    RADIAL = "radial"           # 径向


class GlowIntensity(Enum):
    """发光强度"""
    NONE = 0
    SUBTLE = 1      # 微弱
    NORMAL = 2      # 正常
    STRONG = 3      # 强烈
    INTENSE = 4     # 强烈


def _validate_hex_color(color: str) -> bool:
    """验证十六进制颜色格式
    
    Args:
        color: 颜色字符串
        
    Returns:
        是否有效
        
    Note:
        支持格式: #RGB, #RRGGBB, #RRGGBBAA
    """
    if not isinstance(color, str):
        return False
    # 支持 #RGB, #RRGGBB, #RRGGBBAA 格式
    pattern = r'^#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6}|[A-Fa-f0-9]{8})$'
    return bool(re.match(pattern, color))


def _ensure_tkinter_color(color: str, bg_color: str = "#121212") -> str:
    """确保颜色为Tkinter兼容格式
    
    Args:
        color: 输入颜色
        bg_color: 背景色(用于alpha混合)
        
    Returns:
        Tkinter兼容的#RRGGBB格式
    """
    return to_tkinter_color(color, bg_color)


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """十六进制转RGB
    
    Args:
        hex_color: 十六进制颜色 (支持#RGB, #RRGGBB, #RRGGBBAA)
        
    Returns:
        (R, G, B) 元组
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    elif len(hex_color) == 8:
        # #RRGGBBAA格式，只取RGB部分
        hex_color = hex_color[:6]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """RGB转十六进制
    
    Args:
        rgb: (R, G, B) 元组
        
    Returns:
        十六进制颜色字符串
    """
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, rgb[0])),
        max(0, min(255, rgb[1])),
        max(0, min(255, rgb[2]))
    )


def _interpolate_color(color1: str, color2: str, t: float) -> str:
    """颜色插值
    
    Args:
        color1: 起始颜色
        color2: 结束颜色
        t: 插值因子 (0-1)
        
    Returns:
        插值后的颜色
    """
    rgb1 = _hex_to_rgb(color1)
    rgb2 = _hex_to_rgb(color2)
    
    r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * t)
    g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * t)
    b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * t)
    
    return _rgb_to_hex((r, g, b))


class GradientBorder(tk.Canvas):
    """渐变边框组件
    
    使用Canvas绘制渐变色边框。
    """
    
    # 安全限制
    MAX_BORDER_WIDTH = 20
    MAX_GLOW_SPREAD = 30
    MAX_ANIMATION_DURATION = 10000  # 10秒
    
    def __init__(
        self,
        master,
        width: int = 200,
        height: int = 100,
        border_width: int = 2,
        colors: List[str] = None,
        direction: GradientDirection = GradientDirection.HORIZONTAL,
        corner_radius: int = 8,
        glow_intensity: GlowIntensity = GlowIntensity.NONE,
        glow_color: Optional[str] = None,
        animated: bool = False,
        animation_speed: int = 50,
        bg_color: str = None,
        theme: str = "dark",
        **kwargs
    ):
        """初始化渐变边框
        
        Args:
            master: 父容器
            width: 宽度
            height: 高度
            border_width: 边框宽度
            colors: 渐变颜色列表
            direction: 渐变方向
            corner_radius: 圆角半径
            glow_intensity: 发光强度
            glow_color: 发光颜色
            animated: 是否启用动画
            animation_speed: 动画速度 (ms)
            bg_color: 背景色
            theme: 主题
            **kwargs: 其他参数
        """
        # 参数验证和安全限制
        border_width = max(1, min(border_width, self.MAX_BORDER_WIDTH))
        animation_speed = max(16, min(animation_speed, 1000))
        
        self._width = width
        self._height = height
        self._border_width = border_width
        self._corner_radius = max(0, min(corner_radius, min(width, height) // 2))
        self._direction = direction
        self._glow_intensity = glow_intensity
        self._animated = animated
        self._animation_speed = animation_speed
        self._animation_offset = 0
        self._animation_id = None
        self._theme = theme
        
        # 默认颜色
        if colors is None:
            colors = [ModernColors.DARK_ACCENT, ModernColors.DARK_ACCENT_LIGHT]
        
        # 颜色验证并转换为Tkinter兼容格式
        self._colors = []
        for c in colors[:10]:  # 最多10个颜色
            if _validate_hex_color(c):
                # 转换为Tkinter兼容的#RRGGBB格式
                self._colors.append(_ensure_tkinter_color(c))
        if not self._colors:
            self._colors = ["#8b5cf6", "#a78bfa"]
        
        # 发光颜色
        if glow_color and _validate_hex_color(glow_color):
            self._glow_color = glow_color
        else:
            self._glow_color = self._colors[0]
        
        # 背景色
        if bg_color and _validate_hex_color(bg_color):
            self._bg_color = bg_color
        else:
            self._bg_color = ModernColors.DARK_BG if theme == "dark" else ModernColors.LIGHT_BG
        
        # 计算实际尺寸（包含发光扩散）
        glow_spread = glow_intensity.value * 5
        glow_spread = min(glow_spread, self.MAX_GLOW_SPREAD)
        
        canvas_width = width + glow_spread * 2
        canvas_height = height + glow_spread * 2
        self._glow_spread = glow_spread
        
        super().__init__(
            master,
            width=canvas_width,
            height=canvas_height,
            highlightthickness=0,
            bg=self._bg_color,
            **kwargs
        )
        
        # 内容框架
        self._content_frame = None
        self._create_content_frame()
        
        # 绘制边框
        self._draw_border()
        
        # 启动动画
        if animated:
            self._start_animation()
    
    def _create_content_frame(self):
        """创建内容框架"""
        if _CTK_AVAILABLE:
            self._content_frame = ctk.CTkFrame(
                self,
                fg_color=self._bg_color,
                corner_radius=max(0, self._corner_radius - self._border_width)
            )
        else:
            self._content_frame = tk.Frame(
                self,
                bg=self._bg_color
            )
        
        # 放置在边框内部
        x = self._glow_spread + self._border_width
        y = self._glow_spread + self._border_width
        inner_width = self._width - self._border_width * 2
        inner_height = self._height - self._border_width * 2
        
        self.create_window(
            x, y,
            window=self._content_frame,
            anchor="nw",
            width=inner_width,
            height=inner_height
        )
    
    def _draw_border(self):
        """绘制渐变边框"""
        # 清除现有绘制
        self.delete("border")
        self.delete("glow")
        
        # 绘制发光效果
        if self._glow_intensity != GlowIntensity.NONE:
            self._draw_glow()
        
        # 绘制渐变边框
        steps = max(10, self._width + self._height)  # 渐变步数
        steps = min(steps, 200)  # 性能限制
        
        if self._direction == GradientDirection.HORIZONTAL:
            self._draw_horizontal_gradient(steps)
        elif self._direction == GradientDirection.VERTICAL:
            self._draw_vertical_gradient(steps)
        elif self._direction == GradientDirection.DIAGONAL:
            self._draw_diagonal_gradient(steps)
        else:
            self._draw_radial_gradient()
    
    def _draw_glow(self):
        """绘制发光效果"""
        spread = self._glow_spread
        if spread <= 0:
            return
        
        # 发光层数
        layers = spread
        base_rgb = _hex_to_rgb(self._glow_color)
        
        for i in range(layers, 0, -1):
            # 透明度递减
            alpha = (layers - i) / layers * 0.3
            
            # 混合颜色与背景
            bg_rgb = _hex_to_rgb(self._bg_color)
            blended = (
                int(base_rgb[0] * alpha + bg_rgb[0] * (1 - alpha)),
                int(base_rgb[1] * alpha + bg_rgb[1] * (1 - alpha)),
                int(base_rgb[2] * alpha + bg_rgb[2] * (1 - alpha))
            )
            color = _rgb_to_hex(blended)
            
            # 绘制发光圆角矩形
            offset = spread - i
            self._draw_rounded_rect(
                offset,
                offset,
                self._width + spread * 2 - offset * 2,
                self._height + spread * 2 - offset * 2,
                self._corner_radius + i,
                color,
                "glow"
            )
    
    def _draw_horizontal_gradient(self, steps: int):
        """绘制水平渐变边框"""
        for i in range(steps):
            t = (i + self._animation_offset) % steps / steps
            color = self._get_gradient_color(t)
            
            # 上边框
            x = self._glow_spread + i * self._width / steps
            self.create_line(
                x, self._glow_spread,
                x + self._width / steps + 1, self._glow_spread,
                fill=color, width=self._border_width, tags="border"
            )
            
            # 下边框
            self.create_line(
                x, self._glow_spread + self._height,
                x + self._width / steps + 1, self._glow_spread + self._height,
                fill=color, width=self._border_width, tags="border"
            )
        
        # 左右边框（使用首尾颜色）
        left_color = self._get_gradient_color(self._animation_offset / steps if steps > 0 else 0)
        right_color = self._get_gradient_color((self._animation_offset + steps - 1) % steps / steps if steps > 0 else 1)
        
        self.create_line(
            self._glow_spread, self._glow_spread,
            self._glow_spread, self._glow_spread + self._height,
            fill=left_color, width=self._border_width, tags="border"
        )
        self.create_line(
            self._glow_spread + self._width, self._glow_spread,
            self._glow_spread + self._width, self._glow_spread + self._height,
            fill=right_color, width=self._border_width, tags="border"
        )
    
    def _draw_vertical_gradient(self, steps: int):
        """绘制垂直渐变边框"""
        for i in range(steps):
            t = (i + self._animation_offset) % steps / steps
            color = self._get_gradient_color(t)
            
            # 左边框
            y = self._glow_spread + i * self._height / steps
            self.create_line(
                self._glow_spread, y,
                self._glow_spread, y + self._height / steps + 1,
                fill=color, width=self._border_width, tags="border"
            )
            
            # 右边框
            self.create_line(
                self._glow_spread + self._width, y,
                self._glow_spread + self._width, y + self._height / steps + 1,
                fill=color, width=self._border_width, tags="border"
            )
        
        # 上下边框
        top_color = self._get_gradient_color(self._animation_offset / steps if steps > 0 else 0)
        bottom_color = self._get_gradient_color((self._animation_offset + steps - 1) % steps / steps if steps > 0 else 1)
        
        self.create_line(
            self._glow_spread, self._glow_spread,
            self._glow_spread + self._width, self._glow_spread,
            fill=top_color, width=self._border_width, tags="border"
        )
        self.create_line(
            self._glow_spread, self._glow_spread + self._height,
            self._glow_spread + self._width, self._glow_spread + self._height,
            fill=bottom_color, width=self._border_width, tags="border"
        )
    
    def _draw_diagonal_gradient(self, steps: int):
        """绘制对角渐变边框"""
        # 简化为沿边框走向的渐变
        perimeter = (self._width + self._height) * 2
        half_bw = self._border_width / 2
        
        # 绘制四条边
        current = 0
        
        # 上边
        for i in range(int(self._width)):
            t = ((current + i + self._animation_offset) % steps) / steps
            color = self._get_gradient_color(t)
            x = self._glow_spread + i
            self.create_line(
                x, self._glow_spread + half_bw,
                x + 1, self._glow_spread + half_bw,
                fill=color, width=self._border_width, tags="border"
            )
        current += self._width
        
        # 右边
        for i in range(int(self._height)):
            t = ((current + i + self._animation_offset) % steps) / steps
            color = self._get_gradient_color(t)
            y = self._glow_spread + i
            self.create_line(
                self._glow_spread + self._width - half_bw, y,
                self._glow_spread + self._width - half_bw, y + 1,
                fill=color, width=self._border_width, tags="border"
            )
        current += self._height
        
        # 下边（反向）
        for i in range(int(self._width)):
            t = ((current + i + self._animation_offset) % steps) / steps
            color = self._get_gradient_color(t)
            x = self._glow_spread + self._width - i
            self.create_line(
                x, self._glow_spread + self._height - half_bw,
                x - 1, self._glow_spread + self._height - half_bw,
                fill=color, width=self._border_width, tags="border"
            )
        current += self._width
        
        # 左边（反向）
        for i in range(int(self._height)):
            t = ((current + i + self._animation_offset) % steps) / steps
            color = self._get_gradient_color(t)
            y = self._glow_spread + self._height - i
            self.create_line(
                self._glow_spread + half_bw, y,
                self._glow_spread + half_bw, y - 1,
                fill=color, width=self._border_width, tags="border"
            )
    
    def _draw_radial_gradient(self):
        """绘制径向渐变边框（从中心向外）"""
        # 简化实现：使用单色边框
        color = self._colors[0]
        self._draw_rounded_rect(
            self._glow_spread,
            self._glow_spread,
            self._width,
            self._height,
            self._corner_radius,
            color,
            "border",
            outline_only=True
        )
    
    def _draw_rounded_rect(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
        color: str,
        tags: str,
        outline_only: bool = False
    ):
        """绘制圆角矩形
        
        Args:
            x, y: 左上角坐标
            width, height: 尺寸
            radius: 圆角半径
            color: 颜色
            tags: 标签
            outline_only: 仅绘制轮廓
        """
        radius = min(radius, width / 2, height / 2)
        
        points = [
            x + radius, y,
            x + width - radius, y,
            x + width, y,
            x + width, y + radius,
            x + width, y + height - radius,
            x + width, y + height,
            x + width - radius, y + height,
            x + radius, y + height,
            x, y + height,
            x, y + height - radius,
            x, y + radius,
            x, y,
            x + radius, y
        ]
        
        if outline_only:
            self.create_polygon(
                points,
                outline=color,
                fill="",
                width=self._border_width,
                smooth=True,
                tags=tags
            )
        else:
            self.create_polygon(
                points,
                fill=color,
                outline="",
                smooth=True,
                tags=tags
            )
    
    def _get_gradient_color(self, t: float) -> str:
        """获取渐变颜色
        
        Args:
            t: 位置因子 (0-1)
            
        Returns:
            插值颜色
        """
        if len(self._colors) == 1:
            return self._colors[0]
        
        # 多色渐变
        n = len(self._colors) - 1
        segment = t * n
        idx = int(segment)
        idx = min(idx, n - 1)
        local_t = segment - idx
        
        return _interpolate_color(self._colors[idx], self._colors[idx + 1], local_t)
    
    def _start_animation(self):
        """启动动画"""
        if self._animation_id:
            return
        self._animate()
    
    def _animate(self):
        """动画帧"""
        self._animation_offset = (self._animation_offset + 1) % 100
        self._draw_border()
        self._animation_id = self.after(self._animation_speed, self._animate)
    
    def stop_animation(self):
        """停止动画"""
        if self._animation_id:
            self.after_cancel(self._animation_id)
            self._animation_id = None
    
    def get_content_frame(self):
        """获取内容框架
        
        Returns:
            内容Frame，用于添加子组件
        """
        return self._content_frame
    
    def set_colors(self, colors: List[str]):
        """设置渐变颜色
        
        Args:
            colors: 颜色列表
        """
        validated = []
        for c in colors[:10]:
            if _validate_hex_color(c):
                validated.append(c)
        if validated:
            self._colors = validated
            self._draw_border()
    
    def set_glow_intensity(self, intensity: GlowIntensity):
        """设置发光强度
        
        Args:
            intensity: 发光强度
        """
        self._glow_intensity = intensity
        self._draw_border()
    
    def destroy(self):
        """销毁组件"""
        self.stop_animation()
        super().destroy()


class Divider(tk.Canvas):
    """分隔线组件
    
    支持普通分隔线和渐变分隔线。
    """
    
    def __init__(
        self,
        master,
        orientation: str = "horizontal",
        length: int = 200,
        thickness: int = 1,
        color: str = None,
        gradient_colors: List[str] = None,
        fade_edges: bool = False,
        theme: str = "dark",
        **kwargs
    ):
        """初始化分隔线
        
        Args:
            master: 父容器
            orientation: 方向 ("horizontal" 或 "vertical")
            length: 长度
            thickness: 粗细
            color: 单色
            gradient_colors: 渐变颜色
            fade_edges: 边缘淡出效果
            theme: 主题
            **kwargs: 其他参数
        """
        self._orientation = orientation
        self._length = length
        self._thickness = max(1, min(thickness, 10))
        self._fade_edges = fade_edges
        self._theme = theme
        
        # 颜色
        if color and _validate_hex_color(color):
            self._color = color
        else:
            self._color = ModernColors.DARK_DIVIDER if theme == "dark" else ModernColors.LIGHT_DIVIDER
        
        # 渐变颜色
        self._gradient_colors = None
        if gradient_colors:
            validated = [c for c in gradient_colors[:5] if _validate_hex_color(c)]
            if validated:
                self._gradient_colors = validated
        
        # 尺寸
        if orientation == "horizontal":
            width = length
            height = thickness
        else:
            width = thickness
            height = length
        
        bg_color = ModernColors.DARK_BG if theme == "dark" else ModernColors.LIGHT_BG
        
        super().__init__(
            master,
            width=width,
            height=height,
            highlightthickness=0,
            bg=bg_color,
            **kwargs
        )
        
        self._draw_divider()
    
    def _draw_divider(self):
        """绘制分隔线"""
        self.delete("all")
        
        if self._gradient_colors:
            self._draw_gradient_line()
        elif self._fade_edges:
            self._draw_faded_line()
        else:
            self._draw_solid_line()
    
    def _draw_solid_line(self):
        """绘制实线"""
        if self._orientation == "horizontal":
            self.create_line(
                0, self._thickness / 2,
                self._length, self._thickness / 2,
                fill=self._color,
                width=self._thickness
            )
        else:
            self.create_line(
                self._thickness / 2, 0,
                self._thickness / 2, self._length,
                fill=self._color,
                width=self._thickness
            )
    
    def _draw_faded_line(self):
        """绘制边缘淡出的线"""
        steps = 20
        fade_length = self._length // 4
        
        bg_color = ModernColors.DARK_BG if self._theme == "dark" else ModernColors.LIGHT_BG
        
        for i in range(steps):
            t = i / steps
            
            # 左侧/上侧渐变
            fade_color = _interpolate_color(bg_color, self._color, t)
            pos = t * fade_length
            
            if self._orientation == "horizontal":
                self.create_line(
                    pos, self._thickness / 2,
                    pos + fade_length / steps + 1, self._thickness / 2,
                    fill=fade_color,
                    width=self._thickness
                )
            else:
                self.create_line(
                    self._thickness / 2, pos,
                    self._thickness / 2, pos + fade_length / steps + 1,
                    fill=fade_color,
                    width=self._thickness
                )
            
            # 右侧/下侧渐变
            fade_color = _interpolate_color(self._color, bg_color, t)
            pos = self._length - fade_length + t * fade_length
            
            if self._orientation == "horizontal":
                self.create_line(
                    pos, self._thickness / 2,
                    pos + fade_length / steps + 1, self._thickness / 2,
                    fill=fade_color,
                    width=self._thickness
                )
            else:
                self.create_line(
                    self._thickness / 2, pos,
                    self._thickness / 2, pos + fade_length / steps + 1,
                    fill=fade_color,
                    width=self._thickness
                )
        
        # 中间实线
        if self._orientation == "horizontal":
            self.create_line(
                fade_length, self._thickness / 2,
                self._length - fade_length, self._thickness / 2,
                fill=self._color,
                width=self._thickness
            )
        else:
            self.create_line(
                self._thickness / 2, fade_length,
                self._thickness / 2, self._length - fade_length,
                fill=self._color,
                width=self._thickness
            )
    
    def _draw_gradient_line(self):
        """绘制渐变线"""
        steps = min(self._length, 100)
        
        for i in range(steps):
            t = i / steps
            
            # 多色渐变
            n = len(self._gradient_colors) - 1
            if n > 0:
                segment = t * n
                idx = int(segment)
                idx = min(idx, n - 1)
                local_t = segment - idx
                color = _interpolate_color(
                    self._gradient_colors[idx],
                    self._gradient_colors[idx + 1],
                    local_t
                )
            else:
                color = self._gradient_colors[0]
            
            pos = i * self._length / steps
            
            if self._orientation == "horizontal":
                self.create_line(
                    pos, self._thickness / 2,
                    pos + self._length / steps + 1, self._thickness / 2,
                    fill=color,
                    width=self._thickness
                )
            else:
                self.create_line(
                    self._thickness / 2, pos,
                    self._thickness / 2, pos + self._length / steps + 1,
                    fill=color,
                    width=self._thickness
                )


# 便捷函数
def create_gradient_border(
    master,
    width: int = 200,
    height: int = 100,
    colors: List[str] = None,
    glow: bool = False,
    animated: bool = False,
    theme: str = "dark"
) -> GradientBorder:
    """快速创建渐变边框
    
    Args:
        master: 父容器
        width: 宽度
        height: 高度
        colors: 渐变颜色
        glow: 是否发光
        animated: 是否动画
        theme: 主题
        
    Returns:
        GradientBorder实例
    """
    return GradientBorder(
        master,
        width=width,
        height=height,
        colors=colors,
        glow_intensity=GlowIntensity.NORMAL if glow else GlowIntensity.NONE,
        animated=animated,
        theme=theme
    )


def create_divider(
    master,
    orientation: str = "horizontal",
    length: int = 200,
    gradient: bool = False,
    fade: bool = False,
    theme: str = "dark"
) -> Divider:
    """快速创建分隔线
    
    Args:
        master: 父容器
        orientation: 方向
        length: 长度
        gradient: 是否渐变
        fade: 是否边缘淡出
        theme: 主题
        
    Returns:
        Divider实例
    """
    gradient_colors = None
    if gradient:
        if theme == "dark":
            gradient_colors = [
                ModernColors.DARK_ACCENT,
                ModernColors.DARK_ACCENT_LIGHT
            ]
        else:
            gradient_colors = [
                ModernColors.LIGHT_ACCENT,
                ModernColors.LIGHT_ACCENT_LIGHT
            ]
    
    return Divider(
        master,
        orientation=orientation,
        length=length,
        gradient_colors=gradient_colors,
        fade_edges=fade,
        theme=theme
    )
