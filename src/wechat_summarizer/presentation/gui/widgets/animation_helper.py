"""动画工具类和页面过渡管理器

从 app.py 提取的动画基础设施：
- AnimationHelper: 平滑动画工具（缓动函数、数值插值）
- TransitionManager: 页面滑动过渡动画
"""

from __future__ import annotations

from loguru import logger

from ..utils.display import DisplayHelper


class AnimationHelper:
    """平滑动画工具类 - 高刷新率优化版

    性能优化：
    - 自动检测屏幕刷新率，支持 60Hz/120Hz/144Hz/165Hz/240Hz
    - 动态调整帧率以匹配屏幕
    - 精确帧时间控制（浮点数）
    - 优化的缓动函数
    - 减少不必要的重绘
    """

    # 动态 FPS：根据屏幕刷新率自动调整
    _fps: int | None = None
    _frame_duration: float | None = None
    _initialized: bool = False

    # 最佳动画时长（基于 UX 研究：200-300ms）
    DURATION_FAST = 150  # 快速反馈：微交互
    DURATION_NORMAL = 200  # 标准动画：按钮、卡片
    DURATION_SMOOTH = 250  # 平滑过渡：页面切换
    DURATION_SLOW = 300  # 慢速：强调效果

    @classmethod
    def _ensure_initialized(cls):
        """确保动画参数已初始化"""
        if not cls._initialized:
            cls._fps = DisplayHelper.get_optimal_fps()
            cls._frame_duration = 1000.0 / cls._fps
            cls._initialized = True

            refresh_rate = DisplayHelper.get_refresh_rate()
            if refresh_rate > 60:
                logger.info(f"🎮 动画系统已优化: 屏幕 {refresh_rate}Hz, 动画 {cls._fps}fps")

    @classmethod
    def FPS(cls) -> int:  # noqa: N802
        """获取当前 FPS"""
        cls._ensure_initialized()
        return cls._fps if cls._fps is not None else 60

    @classmethod
    def FRAME_DURATION(cls) -> float:  # noqa: N802
        """获取当前帧时长 (ms)"""
        cls._ensure_initialized()
        return cls._frame_duration if cls._frame_duration is not None else (1000.0 / 60)

    @classmethod
    def get_fps(cls) -> int:
        """获取当前 FPS (兼容方法)"""
        cls._ensure_initialized()
        return cls._fps if cls._fps is not None else 60

    @classmethod
    def get_frame_duration(cls) -> float:
        """获取当前帧时长 (兼容方法)"""
        cls._ensure_initialized()
        return cls._frame_duration if cls._frame_duration is not None else (1000.0 / 60)

    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """缓出三次方 - 用于平滑的结束效果

        推荐用途：退出动画、淡出效果
        """
        return 1 - pow(1 - t, 3)

    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """缓进缓出三次方 - 用于平滑过渡

        推荐用途：页面切换、位置移动
        注意：已优化性能，减少分支预测失败
        """
        t *= 2
        if t < 1:
            return 0.5 * t * t * t
        t -= 2
        return 0.5 * (t * t * t + 2)

    @staticmethod
    def ease_out_expo(t: float) -> float:
        """缓出指数 - 最平滑的减速效果

        推荐用途：所有动画的默认缓动函数
        Material Design 推荐使用
        """
        return 1 if t == 1 else 1 - pow(2, -10 * t)

    @staticmethod
    def ease_out_quart(t: float) -> float:
        """缓出四次方 - 比三次方更平滑

        推荐用途：大型元素移动、页面过渡
        """
        return 1 - pow(1 - t, 4)

    @staticmethod
    def ease_out_back(t: float) -> float:
        """缓出回弹 - 用于弹性效果

        推荐用途：强调性动画（但不要过度使用）
        """
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    @staticmethod
    def lerp(start: float, end: float, t: float) -> float:
        """线性插值"""
        return start + (end - start) * t

    @classmethod
    def animate_value(
        cls,
        root,
        start_val: float,
        end_val: float,
        duration_ms: int,
        callback,
        easing=None,
        on_complete=None,
    ):
        """动画数值变化 - 性能优化版

        优化点：
        - 使用浮点数帧时间，精度更高
        - 减少不必要的计算
        - 预先计算总帧数
        - 缓动函数默认使用最平滑的 ease_out_expo

        Args:
            root: Tkinter root窗口
            start_val: 起始值
            end_val: 结束值
            duration_ms: 动画时长(毫秒)，建议 150-300ms
            callback: 每帧回调函数(current_value)
            easing: 缓动函数，默认 ease_out_expo（最平滑）
            on_complete: 动画完成回调
        """
        if easing is None:
            easing = cls.ease_out_expo  # 使用更平滑的默认缓动

        # 使用浮点数计算总帧数，提高精度
        frame_duration = cls.get_frame_duration()
        total_frames = max(1, int(duration_ms / frame_duration))
        frame_duration_int = int(frame_duration)  # 转为整数用于 after()

        current_frame = [0]

        def update():
            if current_frame[0] >= total_frames:
                # 确保最终值精确
                callback(end_val)
                if on_complete:
                    on_complete()
                return

            # 计算进度（0.0 - 1.0）
            progress = current_frame[0] / total_frames
            eased_progress = easing(progress)
            current_val = cls.lerp(start_val, end_val, eased_progress)
            callback(current_val)

            current_frame[0] += 1
            root.after(frame_duration_int, update)

        update()


class TransitionManager:
    """页面过渡动画管理器 - 性能优化版

    使用 place() 几何管理器实现页面滑入滑出动画

    优化点：
    - 缩短动画时长至 200ms（UX 研究推荐范围）
    - 减少不必要的 update_idletasks() 调用
    - 优化位置计算，减少重绘
    """

    # 动画配置 - 基于 Material Design 和 Apple HIG
    DURATION_MS = 200  # 页面切换推荐 200-250ms
    DIRECTION_LEFT = "left"
    DIRECTION_RIGHT = "right"
    DIRECTION_UP = "up"
    DIRECTION_DOWN = "down"

    @classmethod
    def slide_transition(
        cls,
        root,
        container,
        old_frame,
        new_frame,
        direction: str = "left",
        duration_ms: int | None = None,
        on_complete=None,
    ):
        """执行页面滑动过渡动画

        Args:
            root: Tkinter root 窗口
            container: 页面容器 Frame
            old_frame: 旧页面 Frame (可为 None)
            new_frame: 新页面 Frame
            direction: 滑动方向 ('left', 'right', 'up', 'down')
            duration_ms: 动画时长 (毫秒)
            on_complete: 动画完成回调
        """
        if duration_ms is None:
            duration_ms = cls.DURATION_MS

        # 获取容器尺寸
        container.update_idletasks()
        width = container.winfo_width()
        height = container.winfo_height()

        if width <= 1 or height <= 1:
            # 容器尚未布局，直接显示新页面
            if old_frame:
                old_frame.grid_forget()
            new_frame.grid(row=0, column=0, sticky="nsew")
            if on_complete:
                on_complete()
            return

        # 计算起始和结束位置
        if direction == cls.DIRECTION_LEFT:
            # 新页面从右向左滑入
            new_start_x = width
            new_end_x = 0
            old_end_x = -width
            is_horizontal = True
        elif direction == cls.DIRECTION_RIGHT:
            # 新页面从左向右滑入
            new_start_x = -width
            new_end_x = 0
            old_end_x = width
            is_horizontal = True
        elif direction == cls.DIRECTION_UP:
            # 新页面从下向上滑入
            new_start_y = height
            new_end_y = 0
            old_end_y = -height
            is_horizontal = False
        else:  # direction == cls.DIRECTION_DOWN
            # 新页面从上向下滑入
            new_start_y = -height
            new_end_y = 0
            old_end_y = height
            is_horizontal = False

        # 准备动画：使用 place 定位
        if old_frame and old_frame.winfo_ismapped():
            old_frame.grid_forget()
            old_frame.place(x=0, y=0, relwidth=1, relheight=1)

        if is_horizontal:
            new_frame.place(x=new_start_x, y=0, relwidth=1, relheight=1)
        else:
            new_frame.place(x=0, y=new_start_y, relwidth=1, relheight=1)

        # 执行动画
        def update_position(progress):
            t = AnimationHelper.ease_in_out_cubic(progress)

            if is_horizontal:
                new_x = AnimationHelper.lerp(new_start_x, new_end_x, t)
                new_frame.place(x=int(new_x), y=0, relwidth=1, relheight=1)

                if old_frame and old_frame.winfo_exists():
                    old_x = AnimationHelper.lerp(0, old_end_x, t)
                    old_frame.place(x=int(old_x), y=0, relwidth=1, relheight=1)
            else:
                new_y = AnimationHelper.lerp(new_start_y, new_end_y, t)
                new_frame.place(x=0, y=int(new_y), relwidth=1, relheight=1)

                if old_frame and old_frame.winfo_exists():
                    old_y = AnimationHelper.lerp(0, old_end_y, t)
                    old_frame.place(x=0, y=int(old_y), relwidth=1, relheight=1)

        def on_animation_complete():
            # 清理：切换回 grid 布局
            if old_frame and old_frame.winfo_exists():
                old_frame.place_forget()

            new_frame.place_forget()
            new_frame.grid(row=0, column=0, sticky="nsew")

            if on_complete:
                on_complete()

        # 使用 AnimationHelper 执行动画
        AnimationHelper.animate_value(
            root,
            0.0,
            1.0,
            duration_ms,
            update_position,
            easing=lambda x: x,  # 使用线性，在 update_position 中应用缓动
            on_complete=on_animation_complete,
        )
