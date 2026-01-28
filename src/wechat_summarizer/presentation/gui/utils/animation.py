"""
统一动画管理器 (Animation Engine)
符合2026年设计趋势的高性能动画系统

功能特性:
- 基于时间轴的补间动画(Tween)
- 丰富的缓动函数库
- 动画队列与组合(sequence/parallel)
- 高刷新率适配(60/120/144Hz)
- 属性动画(任意数值属性)
- 关键帧动画

安全措施:
- 动画资源自动释放
- 内存泄漏防护
- CPU使用率监控
- 最大动画数量限制
"""

import tkinter as tk
from typing import (
    Optional, Callable, Dict, List, Any, Union,
    Literal, TypeVar, Generic
)
from dataclasses import dataclass, field
from enum import Enum
import time
import math
import logging
import platform

logger = logging.getLogger(__name__)

T = TypeVar("T", int, float)


class EasingType(Enum):
    """缓动类型"""
    LINEAR = "linear"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_OUT_QUAD = "ease_out_quad"
    EASE_IN_OUT_QUAD = "ease_in_out_quad"
    EASE_IN_CUBIC = "ease_in_cubic"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_IN_OUT_CUBIC = "ease_in_out_cubic"
    EASE_IN_EXPO = "ease_in_expo"
    EASE_OUT_EXPO = "ease_out_expo"
    EASE_IN_OUT_EXPO = "ease_in_out_expo"
    EASE_IN_ELASTIC = "ease_in_elastic"
    EASE_OUT_ELASTIC = "ease_out_elastic"
    EASE_IN_BACK = "ease_in_back"
    EASE_OUT_BACK = "ease_out_back"
    EASE_OUT_BOUNCE = "ease_out_bounce"


class Easing:
    """缓动函数库"""
    
    @staticmethod
    def linear(t: float) -> float:
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_in_expo(t: float) -> float:
        return 0 if t == 0 else pow(2, 10 * t - 10)
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        if t == 0:
            return 0
        if t == 1:
            return 1
        if t < 0.5:
            return pow(2, 20 * t - 10) / 2
        return (2 - pow(2, -20 * t + 10)) / 2
    
    @staticmethod
    def ease_in_elastic(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        if t == 1:
            return 1
        return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        c4 = (2 * math.pi) / 3
        if t == 0:
            return 0
        if t == 1:
            return 1
        return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    @staticmethod
    def ease_in_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return c3 * t * t * t - c1 * t * t
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
    
    @classmethod
    def get(cls, easing_type: EasingType) -> Callable[[float], float]:
        """获取缓动函数"""
        mapping = {
            EasingType.LINEAR: cls.linear,
            EasingType.EASE_IN_QUAD: cls.ease_in_quad,
            EasingType.EASE_OUT_QUAD: cls.ease_out_quad,
            EasingType.EASE_IN_OUT_QUAD: cls.ease_in_out_quad,
            EasingType.EASE_IN_CUBIC: cls.ease_in_cubic,
            EasingType.EASE_OUT_CUBIC: cls.ease_out_cubic,
            EasingType.EASE_IN_OUT_CUBIC: cls.ease_in_out_cubic,
            EasingType.EASE_IN_EXPO: cls.ease_in_expo,
            EasingType.EASE_OUT_EXPO: cls.ease_out_expo,
            EasingType.EASE_IN_OUT_EXPO: cls.ease_in_out_expo,
            EasingType.EASE_IN_ELASTIC: cls.ease_in_elastic,
            EasingType.EASE_OUT_ELASTIC: cls.ease_out_elastic,
            EasingType.EASE_IN_BACK: cls.ease_in_back,
            EasingType.EASE_OUT_BACK: cls.ease_out_back,
            EasingType.EASE_OUT_BOUNCE: cls.ease_out_bounce
        }
        return mapping.get(easing_type, cls.ease_out_cubic)
    
    @staticmethod
    def cubic_bezier(p1x: float, p1y: float, p2x: float, p2y: float) -> Callable[[float], float]:
        """自定义三次贝塞尔曲线"""
        def bezier(t: float) -> float:
            # 简化实现
            cx = 3 * p1x
            bx = 3 * (p2x - p1x) - cx
            ax = 1 - cx - bx
            cy = 3 * p1y
            by = 3 * (p2y - p1y) - cy
            ay = 1 - cy - by
            
            def sample_curve_x(t):
                return ((ax * t + bx) * t + cx) * t
            
            def sample_curve_y(t):
                return ((ay * t + by) * t + cy) * t
            
            # Newton-Raphson迭代求解
            x = t
            for _ in range(8):
                z = sample_curve_x(x) - t
                if abs(z) < 1e-6:
                    break
                d = (3 * ax * x + 2 * bx) * x + cx
                if abs(d) < 1e-6:
                    break
                x = x - z / d
            
            return sample_curve_y(x)
        
        return bezier


@dataclass
class Tween:
    """补间动画"""
    target: Any
    property_name: str
    start_value: float
    end_value: float
    duration: int  # ms
    easing: EasingType = EasingType.EASE_OUT_CUBIC
    delay: int = 0
    on_update: Optional[Callable[[float], None]] = None
    on_complete: Optional[Callable[[], None]] = None
    
    # 内部状态
    _id: str = field(default_factory=lambda: f"tween_{time.time_ns()}")
    _start_time: float = 0
    _is_running: bool = False
    _is_complete: bool = False


class DisplayHelper:
    """显示助手 - 获取最佳刷新率"""
    
    _cached_fps: Optional[int] = None
    
    @classmethod
    def get_optimal_fps(cls) -> int:
        """获取最佳帧率"""
        if cls._cached_fps:
            return cls._cached_fps
        
        fps = 60  # 默认值
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows: 尝试获取显示器刷新率
                try:
                    import ctypes
                    user32 = ctypes.windll.user32
                    dc = user32.GetDC(0)
                    gdi32 = ctypes.windll.gdi32
                    refresh = gdi32.GetDeviceCaps(dc, 116)  # VREFRESH
                    user32.ReleaseDC(0, dc)
                    if refresh > 0:
                        fps = refresh
                except Exception:
                    pass
                    
            elif system == "Darwin":
                # macOS: 默认ProMotion为120Hz
                fps = 120
                
            elif system == "Linux":
                # Linux: 尝试xrandr
                try:
                    import subprocess
                    result = subprocess.run(
                        ["xrandr", "--current"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    for line in result.stdout.split("\n"):
                        if "*" in line:
                            # 解析刷新率
                            parts = line.split()
                            for part in parts:
                                if "*" in part:
                                    rate = float(part.replace("*", "").replace("+", ""))
                                    fps = int(rate)
                                    break
                            break
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"获取刷新率失败: {e}")
        
        # 限制范围
        fps = max(30, min(240, fps))
        cls._cached_fps = fps
        
        logger.info(f"检测到刷新率: {fps}Hz")
        return fps
    
    @classmethod
    def get_frame_time(cls) -> int:
        """获取每帧时间(ms)"""
        return 1000 // cls.get_optimal_fps()


class AnimationEngine:
    """统一动画引擎"""
    
    # 安全限制
    MAX_ANIMATIONS = 50
    MAX_DURATION = 10000  # ms
    
    _instance: Optional["AnimationEngine"] = None
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self._animations: Dict[str, Tween] = {}
        self._sequences: Dict[str, List[Tween]] = {}
        self._is_running = False
        self._frame_time = DisplayHelper.get_frame_time()
        self._loop_id: Optional[str] = None
        
        # 性能监控
        self._frame_count = 0
        self._last_fps_time = time.time()
        self._current_fps = 0
    
    @classmethod
    def get_instance(cls, root: Optional[tk.Tk] = None) -> "AnimationEngine":
        """获取单例实例"""
        if cls._instance is None:
            if root is None:
                raise ValueError("首次调用需要提供root参数")
            cls._instance = cls(root)
        return cls._instance
    
    def animate(
        self,
        target: Any,
        property_name: str,
        end_value: float,
        duration: int = 300,
        easing: EasingType = EasingType.EASE_OUT_CUBIC,
        delay: int = 0,
        on_update: Optional[Callable[[float], None]] = None,
        on_complete: Optional[Callable[[], None]] = None
    ) -> str:
        """创建单个动画"""
        # 限制检查
        if len(self._animations) >= self.MAX_ANIMATIONS:
            logger.warning("动画数量已达上限")
            return ""
        
        duration = min(duration, self.MAX_DURATION)
        
        # 获取起始值
        try:
            if callable(getattr(target, property_name, None)):
                start_value = getattr(target, property_name)()
            else:
                start_value = getattr(target, property_name)
        except Exception:
            start_value = 0
        
        tween = Tween(
            target=target,
            property_name=property_name,
            start_value=float(start_value),
            end_value=float(end_value),
            duration=duration,
            easing=easing,
            delay=delay,
            on_update=on_update,
            on_complete=on_complete
        )
        
        self._animations[tween._id] = tween
        
        if not self._is_running:
            self._start_loop()
        
        return tween._id
    
    def animate_widget(
        self,
        widget: tk.Widget,
        properties: Dict[str, float],
        duration: int = 300,
        easing: EasingType = EasingType.EASE_OUT_CUBIC,
        delay: int = 0,
        on_complete: Optional[Callable[[], None]] = None
    ) -> List[str]:
        """动画化Widget的多个属性"""
        ids = []
        
        for prop, end_value in properties.items():
            tween_id = self.animate(
                target=widget,
                property_name=prop,
                end_value=end_value,
                duration=duration,
                easing=easing,
                delay=delay
            )
            if tween_id:
                ids.append(tween_id)
        
        # 最后一个动画完成时触发回调
        if ids and on_complete:
            last_tween = self._animations.get(ids[-1])
            if last_tween:
                last_tween.on_complete = on_complete
        
        return ids
    
    def sequence(
        self,
        tweens: List[Tween],
        on_complete: Optional[Callable[[], None]] = None
    ) -> str:
        """顺序执行动画"""
        if not tweens:
            return ""
        
        seq_id = f"seq_{time.time_ns()}"
        
        # 计算累积延迟
        cumulative_delay = 0
        for i, tween in enumerate(tweens):
            tween.delay = cumulative_delay
            cumulative_delay += tween.duration + tween.delay
            
            if i == len(tweens) - 1 and on_complete:
                original_complete = tween.on_complete
                def wrapped_complete():
                    if original_complete:
                        original_complete()
                    on_complete()
                tween.on_complete = wrapped_complete
            
            self._animations[tween._id] = tween
        
        self._sequences[seq_id] = tweens
        
        if not self._is_running:
            self._start_loop()
        
        return seq_id
    
    def parallel(
        self,
        tweens: List[Tween],
        on_complete: Optional[Callable[[], None]] = None
    ) -> str:
        """并行执行动画"""
        if not tweens:
            return ""
        
        par_id = f"par_{time.time_ns()}"
        completed_count = [0]
        total_count = len(tweens)
        
        def check_complete():
            completed_count[0] += 1
            if completed_count[0] >= total_count and on_complete:
                on_complete()
        
        for tween in tweens:
            original_complete = tween.on_complete
            def wrapped_complete(orig=original_complete):
                if orig:
                    orig()
                check_complete()
            tween.on_complete = wrapped_complete
            
            self._animations[tween._id] = tween
        
        if not self._is_running:
            self._start_loop()
        
        return par_id
    
    def stop(self, animation_id: str):
        """停止指定动画"""
        if animation_id in self._animations:
            del self._animations[animation_id]
        
        if animation_id in self._sequences:
            for tween in self._sequences[animation_id]:
                if tween._id in self._animations:
                    del self._animations[tween._id]
            del self._sequences[animation_id]
    
    def stop_all(self):
        """停止所有动画"""
        self._animations.clear()
        self._sequences.clear()
        self._stop_loop()
    
    def _start_loop(self):
        """启动动画循环"""
        if self._is_running:
            return
        
        self._is_running = True
        self._loop()
    
    def _stop_loop(self):
        """停止动画循环"""
        self._is_running = False
        if self._loop_id:
            self.root.after_cancel(self._loop_id)
            self._loop_id = None
    
    def _loop(self):
        """动画循环"""
        if not self._is_running or not self._animations:
            self._stop_loop()
            return
        
        current_time = time.time() * 1000
        completed_ids = []
        
        for tween_id, tween in list(self._animations.items()):
            # 初始化开始时间
            if not tween._is_running:
                tween._start_time = current_time + tween.delay
                tween._is_running = True
            
            # 延迟中
            if current_time < tween._start_time:
                continue
            
            # 计算进度
            elapsed = current_time - tween._start_time
            progress = min(1.0, elapsed / tween.duration)
            
            # 应用缓动
            easing_func = Easing.get(tween.easing)
            eased_progress = easing_func(progress)
            
            # 计算当前值
            current_value = tween.start_value + (
                tween.end_value - tween.start_value
            ) * eased_progress
            
            # 更新目标属性
            try:
                if hasattr(tween.target, "configure"):
                    # Tkinter Widget
                    tween.target.configure(**{tween.property_name: current_value})
                elif hasattr(tween.target, tween.property_name):
                    setattr(tween.target, tween.property_name, current_value)
            except Exception as e:
                logger.debug(f"更新属性失败: {e}")
            
            # 更新回调
            if tween.on_update:
                try:
                    tween.on_update(current_value)
                except Exception as e:
                    logger.error(f"更新回调失败: {e}")
            
            # 完成检查
            if progress >= 1.0:
                tween._is_complete = True
                completed_ids.append(tween_id)
                
                if tween.on_complete:
                    try:
                        tween.on_complete()
                    except Exception as e:
                        logger.error(f"完成回调失败: {e}")
        
        # 清理完成的动画
        for tween_id in completed_ids:
            if tween_id in self._animations:
                del self._animations[tween_id]
        
        # FPS统计
        self._frame_count += 1
        if current_time - self._last_fps_time * 1000 > 1000:
            self._current_fps = self._frame_count
            self._frame_count = 0
            self._last_fps_time = current_time / 1000
        
        # 下一帧
        if self._animations:
            self._loop_id = self.root.after(self._frame_time, self._loop)
        else:
            self._stop_loop()
    
    def get_fps(self) -> int:
        """获取当前FPS"""
        return self._current_fps
    
    def get_active_count(self) -> int:
        """获取活动动画数量"""
        return len(self._animations)
    
    def destroy(self):
        """清理资源"""
        self.stop_all()
        AnimationEngine._instance = None


# 便捷函数
def animate(
    target: Any,
    property_name: str,
    end_value: float,
    duration: int = 300,
    easing: EasingType = EasingType.EASE_OUT_CUBIC,
    on_complete: Optional[Callable[[], None]] = None
) -> str:
    """快捷动画函数"""
    engine = AnimationEngine.get_instance()
    return engine.animate(
        target=target,
        property_name=property_name,
        end_value=end_value,
        duration=duration,
        easing=easing,
        on_complete=on_complete
    )


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("动画引擎测试")
    root.geometry("800x600")
    root.configure(bg="#121212")
    
    # 初始化动画引擎
    engine = AnimationEngine(root)
    
    # FPS显示
    fps_label = tk.Label(
        root,
        text="FPS: 0",
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 12)
    )
    fps_label.pack(pady=10)
    
    def update_fps():
        fps_label.config(text=f"FPS: {engine.get_fps()} | 活动动画: {engine.get_active_count()}")
        root.after(500, update_fps)
    
    update_fps()
    
    # 测试对象
    canvas = tk.Canvas(root, width=600, height=400, bg="#1e1e1e", highlightthickness=0)
    canvas.pack(pady=20)
    
    ball = canvas.create_oval(50, 50, 100, 100, fill="#3b82f6", outline="")
    
    class BallAnimator:
        def __init__(self):
            self.x = 50
            self.y = 50
        
        def update(self):
            canvas.coords(ball, self.x, self.y, self.x + 50, self.y + 50)
    
    ball_anim = BallAnimator()
    
    def animate_ball():
        # 创建补间序列
        tween1 = Tween(
            target=ball_anim,
            property_name="x",
            start_value=50,
            end_value=500,
            duration=500,
            easing=EasingType.EASE_OUT_ELASTIC,
            on_update=lambda v: ball_anim.update()
        )
        
        tween2 = Tween(
            target=ball_anim,
            property_name="y",
            start_value=50,
            end_value=300,
            duration=500,
            easing=EasingType.EASE_OUT_BOUNCE,
            on_update=lambda v: ball_anim.update()
        )
        
        tween3 = Tween(
            target=ball_anim,
            property_name="x",
            start_value=500,
            end_value=50,
            duration=500,
            easing=EasingType.EASE_IN_OUT_CUBIC,
            on_update=lambda v: ball_anim.update()
        )
        
        tween4 = Tween(
            target=ball_anim,
            property_name="y",
            start_value=300,
            end_value=50,
            duration=500,
            easing=EasingType.EASE_IN_OUT_CUBIC,
            on_update=lambda v: ball_anim.update()
        )
        
        engine.sequence([tween1, tween2, tween3, tween4], on_complete=animate_ball)
    
    # 开始按钮
    btn = tk.Button(
        root,
        text="开始动画",
        command=animate_ball,
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        relief=tk.FLAT,
        padx=20,
        pady=10
    )
    btn.pack(pady=10)
    
    # 停止按钮
    stop_btn = tk.Button(
        root,
        text="停止所有",
        command=engine.stop_all,
        bg="#ef4444",
        fg="#ffffff",
        font=("Segoe UI", 12),
        relief=tk.FLAT,
        padx=20,
        pady=10
    )
    stop_btn.pack(pady=5)
    
    root.mainloop()
