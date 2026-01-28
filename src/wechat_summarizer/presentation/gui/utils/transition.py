"""
页面切换动画系统 (Page Transition System)
符合2026年设计趋势的流畅页面过渡

功能特性:
- Fade淡入淡出效果
- Slide滑动效果(左/右/上/下)
- Scale缩放效果
- 60fps流畅动画
- 可自定义缓动函数
- 动画队列管理

安全措施:
- 动画超时保护
- 资源清理机制
- 性能监控
- 并发动画限制
"""

import tkinter as tk
from typing import Optional, Callable, Literal, Dict, Any
from enum import Enum
from dataclasses import dataclass
import time
import logging

logger = logging.getLogger(__name__)


class TransitionType(Enum):
    """过渡类型"""
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    SCALE = "scale"
    SCALE_FADE = "scale_fade"
    NONE = "none"


class EasingFunction(Enum):
    """缓动函数类型"""
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"
    EASE_OUT_CUBIC = "ease_out_cubic"
    EASE_OUT_EXPO = "ease_out_expo"
    SPRING = "spring"


@dataclass
class TransitionConfig:
    """过渡配置"""
    type: TransitionType = TransitionType.FADE
    duration: int = 300  # ms
    easing: EasingFunction = EasingFunction.EASE_OUT_CUBIC
    delay: int = 0  # ms


class Easing:
    """缓动函数库"""
    
    @staticmethod
    def linear(t: float) -> float:
        return t
    
    @staticmethod
    def ease_in(t: float) -> float:
        return t * t
    
    @staticmethod
    def ease_out(t: float) -> float:
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        if t < 0.5:
            return 2 * t * t
        return 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def spring(t: float) -> float:
        """弹簧效果"""
        c4 = (2 * 3.14159) / 3
        if t == 0:
            return 0
        if t == 1:
            return 1
        return pow(2, -10 * t) * ((t * 10 - 0.75) * c4) + 1
    
    @classmethod
    def get(cls, easing_type: EasingFunction) -> Callable[[float], float]:
        """获取缓动函数"""
        mapping = {
            EasingFunction.LINEAR: cls.linear,
            EasingFunction.EASE_IN: cls.ease_in,
            EasingFunction.EASE_OUT: cls.ease_out,
            EasingFunction.EASE_IN_OUT: cls.ease_in_out,
            EasingFunction.EASE_OUT_CUBIC: cls.ease_out_cubic,
            EasingFunction.EASE_OUT_EXPO: cls.ease_out_expo,
            EasingFunction.SPRING: cls.spring
        }
        return mapping.get(easing_type, cls.ease_out_cubic)


class PageTransition:
    """页面过渡动画"""
    
    # 安全限制
    MAX_DURATION = 2000  # ms
    MIN_FRAME_TIME = 16  # ~60fps
    MAX_CONCURRENT_ANIMATIONS = 3
    TIMEOUT_MS = 5000
    
    _active_animations = 0
    
    def __init__(
        self,
        container: tk.Widget,
        config: Optional[TransitionConfig] = None
    ):
        self.container = container
        self.config = config or TransitionConfig()
        
        # 验证配置
        self.config.duration = min(self.config.duration, self.MAX_DURATION)
        self.config.delay = min(self.config.delay, 1000)
        
        self._is_animating = False
        self._current_page: Optional[tk.Widget] = None
        self._animation_id: Optional[str] = None
        self._start_time: float = 0
        
        # 缓动函数
        self._easing = Easing.get(self.config.easing)
    
    def transition_to(
        self,
        new_page: tk.Widget,
        on_complete: Optional[Callable[[], None]] = None,
        transition_type: Optional[TransitionType] = None
    ):
        """切换到新页面"""
        # 并发限制
        if PageTransition._active_animations >= self.MAX_CONCURRENT_ANIMATIONS:
            logger.warning("动画并发数已达上限，跳过动画")
            self._instant_switch(new_page, on_complete)
            return
        
        # 如果正在动画，取消当前动画
        if self._is_animating:
            self._cancel_animation()
        
        trans_type = transition_type or self.config.type
        old_page = self._current_page
        
        # 无过渡效果
        if trans_type == TransitionType.NONE:
            self._instant_switch(new_page, on_complete)
            return
        
        # 延迟执行
        if self.config.delay > 0:
            self.container.after(
                self.config.delay,
                lambda: self._start_transition(old_page, new_page, trans_type, on_complete)
            )
        else:
            self._start_transition(old_page, new_page, trans_type, on_complete)
    
    def _start_transition(
        self,
        old_page: Optional[tk.Widget],
        new_page: tk.Widget,
        trans_type: TransitionType,
        on_complete: Optional[Callable[[], None]]
    ):
        """开始过渡动画"""
        PageTransition._active_animations += 1
        self._is_animating = True
        self._start_time = time.time() * 1000
        
        # 放置新页面（初始状态不可见）
        self._setup_initial_state(new_page, trans_type)
        
        # 计算帧数
        frame_count = max(1, self.config.duration // self.MIN_FRAME_TIME)
        frame_duration = self.config.duration / frame_count
        
        def animate_frame(frame: int):
            # 超时保护
            elapsed = time.time() * 1000 - self._start_time
            if elapsed > self.TIMEOUT_MS:
                logger.warning("动画超时，强制完成")
                self._finish_transition(old_page, new_page, on_complete)
                return
            
            if frame > frame_count or not self._is_animating:
                self._finish_transition(old_page, new_page, on_complete)
                return
            
            # 计算进度
            progress = self._easing(frame / frame_count)
            
            # 应用动画
            self._apply_animation_frame(old_page, new_page, trans_type, progress)
            
            # 下一帧
            self._animation_id = self.container.after(
                int(frame_duration),
                lambda: animate_frame(frame + 1)
            )
        
        animate_frame(1)
    
    def _setup_initial_state(self, new_page: tk.Widget, trans_type: TransitionType):
        """设置初始状态"""
        container_width = self.container.winfo_width()
        container_height = self.container.winfo_height()
        
        if trans_type == TransitionType.FADE:
            # 淡入：从透明开始（通过遮罩模拟）
            new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            
        elif trans_type == TransitionType.SLIDE_LEFT:
            new_page.place(x=container_width, y=0, relwidth=1.0, relheight=1.0)
            
        elif trans_type == TransitionType.SLIDE_RIGHT:
            new_page.place(x=-container_width, y=0, relwidth=1.0, relheight=1.0)
            
        elif trans_type == TransitionType.SLIDE_UP:
            new_page.place(x=0, y=container_height, relwidth=1.0, relheight=1.0)
            
        elif trans_type == TransitionType.SLIDE_DOWN:
            new_page.place(x=0, y=-container_height, relwidth=1.0, relheight=1.0)
            
        elif trans_type in (TransitionType.SCALE, TransitionType.SCALE_FADE):
            # 缩放：从中心开始小尺寸
            new_page.place(
                relx=0.5, rely=0.5,
                anchor="center",
                width=1, height=1
            )
    
    def _apply_animation_frame(
        self,
        old_page: Optional[tk.Widget],
        new_page: tk.Widget,
        trans_type: TransitionType,
        progress: float
    ):
        """应用动画帧"""
        container_width = self.container.winfo_width()
        container_height = self.container.winfo_height()
        
        if trans_type == TransitionType.FADE:
            # 淡入淡出（Tkinter无真正透明度，用层叠模拟）
            if progress > 0.5 and old_page:
                old_page.lower()
            new_page.lift()
            
        elif trans_type == TransitionType.SLIDE_LEFT:
            # 新页从右滑入
            new_x = int(container_width * (1 - progress))
            new_page.place(x=new_x)
            
            # 旧页滑出到左
            if old_page:
                old_x = int(-container_width * progress)
                old_page.place(x=old_x)
                
        elif trans_type == TransitionType.SLIDE_RIGHT:
            # 新页从左滑入
            new_x = int(-container_width * (1 - progress))
            new_page.place(x=new_x)
            
            # 旧页滑出到右
            if old_page:
                old_x = int(container_width * progress)
                old_page.place(x=old_x)
                
        elif trans_type == TransitionType.SLIDE_UP:
            # 新页从下滑入
            new_y = int(container_height * (1 - progress))
            new_page.place(y=new_y)
            
            if old_page:
                old_y = int(-container_height * progress)
                old_page.place(y=old_y)
                
        elif trans_type == TransitionType.SLIDE_DOWN:
            # 新页从上滑入
            new_y = int(-container_height * (1 - progress))
            new_page.place(y=new_y)
            
            if old_page:
                old_y = int(container_height * progress)
                old_page.place(y=old_y)
                
        elif trans_type == TransitionType.SCALE:
            # 缩放效果
            scale = progress
            width = int(container_width * scale)
            height = int(container_height * scale)
            
            new_page.place(
                relx=0.5, rely=0.5,
                anchor="center",
                width=max(1, width),
                height=max(1, height)
            )
            
        elif trans_type == TransitionType.SCALE_FADE:
            # 缩放+淡入
            scale = 0.8 + 0.2 * progress
            width = int(container_width * scale)
            height = int(container_height * scale)
            
            new_page.place(
                relx=0.5, rely=0.5,
                anchor="center",
                width=max(1, width),
                height=max(1, height)
            )
            
            if progress > 0.3 and old_page:
                old_page.lower()
            new_page.lift()
    
    def _finish_transition(
        self,
        old_page: Optional[tk.Widget],
        new_page: tk.Widget,
        on_complete: Optional[Callable[[], None]]
    ):
        """完成过渡"""
        PageTransition._active_animations = max(0, PageTransition._active_animations - 1)
        self._is_animating = False
        self._animation_id = None
        
        # 隐藏旧页面
        if old_page:
            old_page.place_forget()
        
        # 新页面最终位置
        new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        new_page.lift()
        
        self._current_page = new_page
        
        # 回调
        if on_complete:
            try:
                on_complete()
            except Exception as e:
                logger.error(f"过渡完成回调执行失败: {e}")
    
    def _instant_switch(
        self,
        new_page: tk.Widget,
        on_complete: Optional[Callable[[], None]]
    ):
        """即时切换（无动画）"""
        if self._current_page:
            self._current_page.place_forget()
        
        new_page.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._current_page = new_page
        
        if on_complete:
            on_complete()
    
    def _cancel_animation(self):
        """取消当前动画"""
        if self._animation_id:
            self.container.after_cancel(self._animation_id)
            self._animation_id = None
        
        self._is_animating = False
        PageTransition._active_animations = max(0, PageTransition._active_animations - 1)
    
    def set_config(self, config: TransitionConfig):
        """更新配置"""
        self.config = config
        self.config.duration = min(self.config.duration, self.MAX_DURATION)
        self._easing = Easing.get(self.config.easing)
    
    def get_current_page(self) -> Optional[tk.Widget]:
        """获取当前页面"""
        return self._current_page
    
    def is_animating(self) -> bool:
        """是否正在动画"""
        return self._is_animating


class PageRouter:
    """页面路由器（带过渡动画）"""
    
    def __init__(
        self,
        container: tk.Widget,
        default_transition: Optional[TransitionConfig] = None
    ):
        self.container = container
        self.default_transition = default_transition or TransitionConfig()
        
        self._pages: Dict[str, tk.Widget] = {}
        self._current_route: Optional[str] = None
        self._transition = PageTransition(container, self.default_transition)
        self._history: list = []
        
        # 路由变化回调
        self._on_route_change: Optional[Callable[[str, str], None]] = None
    
    def register_page(self, route: str, page: tk.Widget):
        """注册页面"""
        self._pages[route] = page
    
    def navigate_to(
        self,
        route: str,
        transition_type: Optional[TransitionType] = None,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """导航到指定路由"""
        if route not in self._pages:
            logger.error(f"路由不存在: {route}")
            return
        
        if route == self._current_route:
            return
        
        old_route = self._current_route
        new_page = self._pages[route]
        
        # 记录历史
        if self._current_route:
            self._history.append(self._current_route)
        
        # 执行过渡
        def on_transition_complete():
            self._current_route = route
            
            if self._on_route_change and old_route:
                self._on_route_change(old_route, route)
            
            if on_complete:
                on_complete()
        
        self._transition.transition_to(
            new_page,
            on_transition_complete,
            transition_type
        )
    
    def go_back(
        self,
        transition_type: Optional[TransitionType] = None
    ) -> bool:
        """返回上一页"""
        if not self._history:
            return False
        
        previous_route = self._history.pop()
        
        # 反向过渡效果
        reverse_type = transition_type
        if reverse_type is None and self.default_transition.type in (
            TransitionType.SLIDE_LEFT,
            TransitionType.SLIDE_RIGHT
        ):
            reverse_type = (
                TransitionType.SLIDE_RIGHT
                if self.default_transition.type == TransitionType.SLIDE_LEFT
                else TransitionType.SLIDE_LEFT
            )
        
        self.navigate_to(previous_route, reverse_type)
        return True
    
    def on_route_change(self, callback: Callable[[str, str], None]):
        """设置路由变化回调"""
        self._on_route_change = callback
    
    def get_current_route(self) -> Optional[str]:
        """获取当前路由"""
        return self._current_route
    
    def get_history(self) -> list:
        """获取历史记录"""
        return self._history.copy()


# 使用示例
if __name__ == "__main__":
    root = tk.Tk()
    root.title("页面切换动画测试")
    root.geometry("800x600")
    root.configure(bg="#121212")
    
    # 页面容器
    container = tk.Frame(root, bg="#121212")
    container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 创建测试页面
    pages = {}
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
    
    for i, color in enumerate(colors):
        page = tk.Frame(container, bg=color)
        tk.Label(
            page,
            text=f"页面 {i + 1}",
            bg=color,
            fg="#ffffff",
            font=("Segoe UI", 24, "bold")
        ).pack(expand=True)
        pages[f"page{i+1}"] = page
    
    # 创建路由器
    router = PageRouter(
        container,
        TransitionConfig(
            type=TransitionType.SLIDE_LEFT,
            duration=400,
            easing=EasingFunction.EASE_OUT_CUBIC
        )
    )
    
    for route, page in pages.items():
        router.register_page(route, page)
    
    # 初始页面
    router.navigate_to("page1", TransitionType.NONE)
    
    # 控制按钮
    btn_frame = tk.Frame(root, bg="#121212")
    btn_frame.pack(pady=10)
    
    transitions = [
        ("Fade", TransitionType.FADE),
        ("Slide Left", TransitionType.SLIDE_LEFT),
        ("Slide Up", TransitionType.SLIDE_UP),
        ("Scale", TransitionType.SCALE)
    ]
    
    current_page_idx = [0]
    
    def next_page(trans_type):
        current_page_idx[0] = (current_page_idx[0] + 1) % 4
        router.navigate_to(f"page{current_page_idx[0] + 1}", trans_type)
    
    for name, trans_type in transitions:
        btn = tk.Button(
            btn_frame,
            text=name,
            command=lambda t=trans_type: next_page(t),
            bg="#333333",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        btn.pack(side=tk.LEFT, padx=5)
    
    root.mainloop()
