"""动态渐变色系统 - 2026 UI设计趋势

提供渐变色生成、渐变动画引擎功能，支持：
- 线性渐变 (Linear Gradient)
- 径向渐变 (Radial Gradient)
- 渐变动画 (带可配置速度)

安全审查：
- 参数边界验证，防止资源耗尽
- 动画帧率限制在合理范围
"""
from __future__ import annotations

import colorsys
import math
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, Tuple, Union

from ..styles.colors import hex_to_rgb


class GradientType(Enum):
    """渐变类型枚举"""
    LINEAR = "linear"
    RADIAL = "radial"
    CONIC = "conic"


class EasingFunction(Enum):
    """缓动函数枚举"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


@dataclass
class GradientStop:
    """渐变色停止点"""
    color: str  # 十六进制颜色
    position: float  # 位置 (0.0 - 1.0)
    
    def __post_init__(self):
        """验证参数边界"""
        self.position = max(0.0, min(1.0, self.position))


@dataclass
class GradientConfig:
    """渐变配置"""
    type: GradientType = GradientType.LINEAR
    stops: List[GradientStop] = None
    angle: float = 0.0  # 角度 (0-360度，仅线性渐变)
    center: Tuple[float, float] = (0.5, 0.5)  # 中心点 (仅径向渐变)
    
    def __post_init__(self):
        if self.stops is None:
            self.stops = []
        # 角度限制在 0-360
        self.angle = self.angle % 360


class GradientManager:
    """渐变色管理器
    
    负责生成和管理渐变色，支持动画效果。
    """
    
    # 安全限制
    MAX_STOPS = 10  # 最大渐变停止点数量
    MAX_FPS = 144   # 最大动画帧率
    MIN_FPS = 10    # 最小动画帧率
    
    def __init__(self):
        self._active_animations: dict = {}
        self._animation_id_counter = 0
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB"""
        return hex_to_rgb(hex_color)
    
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """将RGB转换为十六进制颜色"""
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02x}{g:02x}{b:02x}"
    
    @staticmethod
    def interpolate_color(color1: str, color2: str, t: float) -> str:
        """在两种颜色之间插值
        
        Args:
            color1: 起始颜色 (十六进制)
            color2: 结束颜色 (十六进制)
            t: 插值系数 (0.0 - 1.0)
            
        Returns:
            str: 插值后的颜色 (十六进制)
        """
        t = max(0.0, min(1.0, t))
        
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        
        return GradientManager.rgb_to_hex(r, g, b)
    
    def create_linear_gradient(
        self,
        colors: List[str],
        steps: int = 10,
        angle: float = 0.0
    ) -> List[str]:
        """创建线性渐变色列表
        
        Args:
            colors: 渐变颜色列表 (至少2个)
            steps: 渐变步数
            angle: 渐变角度 (未在颜色计算中使用，仅用于配置)
            
        Returns:
            List[str]: 渐变色列表
        """
        if len(colors) < 2:
            return colors if colors else []
        
        # 安全限制
        steps = max(2, min(100, steps))
        
        result = []
        total_segments = len(colors) - 1
        steps_per_segment = steps // total_segments
        
        for i in range(total_segments):
            start_color = colors[i]
            end_color = colors[i + 1]
            
            segment_steps = steps_per_segment
            if i == total_segments - 1:
                segment_steps = steps - len(result)
            
            for j in range(segment_steps):
                t = j / max(1, segment_steps - 1) if segment_steps > 1 else 0
                result.append(self.interpolate_color(start_color, end_color, t))
        
        return result
    
    def create_radial_gradient(
        self,
        colors: List[str],
        steps: int = 10,
        center: Tuple[float, float] = (0.5, 0.5)
    ) -> List[str]:
        """创建径向渐变色列表
        
        Args:
            colors: 渐变颜色列表 (从中心到边缘)
            steps: 渐变步数
            center: 中心点位置 (0.0-1.0, 0.0-1.0)
            
        Returns:
            List[str]: 渐变色列表 (从中心向外)
        """
        return self.create_linear_gradient(colors, steps)
    
    def get_color_at_position(
        self,
        config: GradientConfig,
        position: float
    ) -> str:
        """获取渐变中指定位置的颜色
        
        Args:
            config: 渐变配置
            position: 位置 (0.0 - 1.0)
            
        Returns:
            str: 该位置的颜色
        """
        if not config.stops:
            return "#000000"
        
        position = max(0.0, min(1.0, position))
        
        # 按位置排序停止点
        stops = sorted(config.stops, key=lambda s: s.position)
        
        # 查找位置所在的区间
        if position <= stops[0].position:
            return stops[0].color
        if position >= stops[-1].position:
            return stops[-1].color
        
        for i in range(len(stops) - 1):
            if stops[i].position <= position <= stops[i + 1].position:
                segment_length = stops[i + 1].position - stops[i].position
                if segment_length == 0:
                    return stops[i].color
                t = (position - stops[i].position) / segment_length
                return self.interpolate_color(stops[i].color, stops[i + 1].color, t)
        
        return stops[-1].color


class GradientAnimator:
    """渐变动画控制器
    
    提供渐变色的动画效果，如色彩呼吸、流动等。
    
    安全限制：
    - 帧率限制在 10-144 fps
    - 单个动画最长持续时间限制
    """
    
    MAX_DURATION = 60.0  # 最大动画持续时间（秒）
    MAX_FPS = 144
    MIN_FPS = 10
    
    def __init__(self, fps: int = 60):
        """初始化动画控制器
        
        Args:
            fps: 目标帧率 (会被限制在合理范围内)
        """
        self._fps = max(self.MIN_FPS, min(self.MAX_FPS, fps))
        self._running = False
        self._current_animation_id = 0
        self._animations: dict = {}
    
    @property
    def fps(self) -> int:
        return self._fps
    
    @fps.setter
    def fps(self, value: int):
        self._fps = max(self.MIN_FPS, min(self.MAX_FPS, value))
    
    @staticmethod
    def apply_easing(t: float, easing: EasingFunction) -> float:
        """应用缓动函数
        
        Args:
            t: 原始进度 (0.0 - 1.0)
            easing: 缓动函数类型
            
        Returns:
            float: 缓动后的进度
        """
        t = max(0.0, min(1.0, t))
        
        if easing == EasingFunction.LINEAR:
            return t
        elif easing == EasingFunction.EASE_IN:
            return t * t
        elif easing == EasingFunction.EASE_OUT:
            return 1 - (1 - t) * (1 - t)
        elif easing == EasingFunction.EASE_IN_OUT:
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - pow(-2 * t + 2, 2) / 2
        return t
    
    def create_breathing_animation(
        self,
        base_color: str,
        intensity: float = 0.2,
        duration: float = 2.0,
        callback: Optional[Callable[[str], None]] = None
    ) -> int:
        """创建呼吸效果动画
        
        颜色会在基础色周围轻微变化，产生呼吸效果。
        
        Args:
            base_color: 基础颜色
            intensity: 强度 (0.0 - 1.0)
            duration: 周期时长（秒）
            callback: 每帧回调函数
            
        Returns:
            int: 动画ID
        """
        intensity = max(0.0, min(1.0, intensity))
        duration = max(0.5, min(self.MAX_DURATION, duration))
        
        self._current_animation_id += 1
        anim_id = self._current_animation_id
        
        r, g, b = hex_to_rgb(base_color)
        
        def get_frame_color(progress: float) -> str:
            # 使用正弦波产生呼吸效果
            wave = math.sin(progress * 2 * math.pi)
            factor = 1.0 + wave * intensity * 0.3
            
            new_r = max(0, min(255, int(r * factor)))
            new_g = max(0, min(255, int(g * factor)))
            new_b = max(0, min(255, int(b * factor)))
            
            return GradientManager.rgb_to_hex(new_r, new_g, new_b)
        
        self._animations[anim_id] = {
            "type": "breathing",
            "duration": duration,
            "get_color": get_frame_color,
            "callback": callback,
            "start_time": None,
            "running": False
        }
        
        return anim_id
    
    def create_color_flow_animation(
        self,
        colors: List[str],
        duration: float = 3.0,
        loop: bool = True,
        easing: EasingFunction = EasingFunction.EASE_IN_OUT,
        callback: Optional[Callable[[str], None]] = None
    ) -> int:
        """创建颜色流动动画
        
        颜色在列表中流动变化。
        
        Args:
            colors: 颜色列表
            duration: 完整周期时长（秒）
            loop: 是否循环
            easing: 缓动函数
            callback: 每帧回调函数
            
        Returns:
            int: 动画ID
        """
        if len(colors) < 2:
            colors = colors + colors if colors else ["#000000", "#000000"]
        
        duration = max(0.5, min(self.MAX_DURATION, duration))
        
        self._current_animation_id += 1
        anim_id = self._current_animation_id
        
        manager = GradientManager()
        
        def get_frame_color(progress: float) -> str:
            eased_progress = self.apply_easing(progress, easing)
            total_segments = len(colors) - 1
            segment_progress = eased_progress * total_segments
            segment_index = min(int(segment_progress), total_segments - 1)
            local_progress = segment_progress - segment_index
            
            return manager.interpolate_color(
                colors[segment_index],
                colors[segment_index + 1],
                local_progress
            )
        
        self._animations[anim_id] = {
            "type": "color_flow",
            "duration": duration,
            "loop": loop,
            "get_color": get_frame_color,
            "callback": callback,
            "start_time": None,
            "running": False
        }
        
        return anim_id
    
    def get_current_color(self, anim_id: int) -> Optional[str]:
        """获取动画当前颜色
        
        Args:
            anim_id: 动画ID
            
        Returns:
            Optional[str]: 当前颜色，如果动画不存在则返回None
        """
        if anim_id not in self._animations:
            return None
        
        anim = self._animations[anim_id]
        
        if anim["start_time"] is None:
            anim["start_time"] = time.time()
        
        elapsed = time.time() - anim["start_time"]
        duration = anim["duration"]
        
        if anim.get("loop", True):
            progress = (elapsed % duration) / duration
        else:
            progress = min(1.0, elapsed / duration)
        
        return anim["get_color"](progress)
    
    def stop_animation(self, anim_id: int):
        """停止指定动画
        
        Args:
            anim_id: 动画ID
        """
        if anim_id in self._animations:
            self._animations[anim_id]["running"] = False
            del self._animations[anim_id]
    
    def stop_all_animations(self):
        """停止所有动画"""
        self._animations.clear()


# 便捷函数
def create_gradient(
    colors: List[str],
    gradient_type: str = "linear",
    steps: int = 10
) -> List[str]:
    """快速创建渐变色列表
    
    Args:
        colors: 渐变颜色列表
        gradient_type: 渐变类型 ("linear" 或 "radial")
        steps: 渐变步数
        
    Returns:
        List[str]: 渐变色列表
    """
    manager = GradientManager()
    
    if gradient_type == "radial":
        return manager.create_radial_gradient(colors, steps)
    return manager.create_linear_gradient(colors, steps)


def interpolate(color1: str, color2: str, t: float) -> str:
    """快速颜色插值
    
    Args:
        color1: 起始颜色
        color2: 结束颜色
        t: 插值系数 (0.0 - 1.0)
        
    Returns:
        str: 插值后的颜色
    """
    return GradientManager.interpolate_color(color1, color2, t)
