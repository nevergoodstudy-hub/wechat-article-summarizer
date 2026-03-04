"""启动画面

带真实进度跟踪的加载界面：
- 无边框窗口
- Logo 和标题
- 带呼吸效果的进度条
- 启动步骤文字
- 线程安全的进度更新
"""

from __future__ import annotations

import contextlib
from datetime import datetime

import customtkinter as ctk
from loguru import logger

from ....shared.constants import VERSION
from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from .animation_helper import AnimationHelper


class StartupTask:
    """启动任务定义

    每个任务包含名称、权重和执行函数
    """

    def __init__(self, name: str, weight: int, func, description: str = ""):
        self.name = name
        self.weight = weight  # 任务权重，用于计算进度百分比
        self.func = func
        self.description = description
        self.completed = False
        self.error: str | None = None


class SplashScreen:
    """启动画面 - 带真实进度跟踪的加载界面

    Features:
    - 无边框窗口
    - Logo 和标题
    - 副标题
    - 带呼吸效果的进度条，显示真实任务进度
    - 启动步骤文字显示当前正在执行的任务
    - 线程安全的进度更新
    """

    def __init__(self, root):
        """创建启动画面

        Args:
            root: 主窗口 (CTk)
        """
        self.root = root
        self._progress = 0
        self._target_progress = 0  # 目标进度，用于平滑动画
        self._closed = False
        self._breathing_phase = 0
        self._breathing_id = None
        self._progress_animation_id = None
        self._tasks: list[StartupTask] = []
        self._total_weight = 0
        self._completed_weight = 0

        # 创建顶层窗口
        self.window = ctk.CTkToplevel(root)
        self.window.withdraw()  # 先隐藏
        self.window.overrideredirect(True)  # 无边框
        self.window.attributes("-topmost", True)

        # 窗口尺寸和位置
        width = 520
        height = 360
        screen_w = self.window.winfo_screenwidth()
        screen_h = self.window.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.window.geometry(f"{width}x{height}+{x}+{y}")

        # 主容器
        self.container = ctk.CTkFrame(
            self.window,
            corner_radius=Spacing.RADIUS_XL,
            fg_color=ModernColors.DARK_BG,
            border_width=1,
            border_color=ModernColors.DARK_BORDER,
        )
        self.container.pack(fill="both", expand=True)

        # 内容区
        content = ctk.CTkFrame(self.container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=30)

        # Logo/标题
        self.title_label = ctk.CTkLabel(
            content,
            text="📰 文章助手",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=ModernColors.DARK_ACCENT,
        )
        self.title_label.pack(pady=(20, 5))

        # 副标题
        self.subtitle_label = ctk.CTkLabel(
            content,
            text="WeChat Article Summarizer",
            font=ctk.CTkFont(size=14),
            text_color=ModernColors.DARK_TEXT_SECONDARY,
        )
        self.subtitle_label.pack(pady=(0, 30))

        # 进度条容器
        progress_container = ctk.CTkFrame(content, fg_color="transparent")
        progress_container.pack(fill="x", pady=10)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            progress_container,
            width=400,
            height=10,
            corner_radius=5,
            fg_color=ModernColors.DARK_CARD,
            progress_color=ModernColors.DARK_ACCENT,
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)

        # 进度百分比标签
        self.percent_label = ctk.CTkLabel(
            progress_container,
            text="0%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ModernColors.DARK_ACCENT,
        )
        self.percent_label.pack(pady=(2, 0))

        # 状态文字
        self.status_label = ctk.CTkLabel(
            content,
            text="正在准备启动...",
            font=ctk.CTkFont(size=13),
            text_color=ModernColors.DARK_TEXT_SECONDARY,
        )
        self.status_label.pack(pady=(15, 5))

        # 详细状态文字
        self.detail_label = ctk.CTkLabel(
            content, text="", font=ctk.CTkFont(size=10), text_color=ModernColors.DARK_TEXT_MUTED
        )
        self.detail_label.pack(pady=(0, 10))

        # 底部信息容器
        footer_frame = ctk.CTkFrame(content, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", pady=(0, 5))

        # 版权信息 - 标准格式: Copyright © [dates] [owner]
        current_year = datetime.now().year
        copyright_text = f"© 2024-{current_year} WeChat Article Summarizer"
        self.copyright_label = ctk.CTkLabel(
            footer_frame,
            text=copyright_text,
            font=ctk.CTkFont(size=9),
            text_color=ModernColors.DARK_TEXT_MUTED,
        )
        self.copyright_label.pack(pady=(0, 2))

        # 版本信息和许可证
        version_license_text = f"v{VERSION} | MIT License"
        self.version_label = ctk.CTkLabel(
            footer_frame,
            text=version_license_text,
            font=ctk.CTkFont(size=9),
            text_color=ModernColors.DARK_TEXT_MUTED,
        )
        self.version_label.pack()

    def add_task(self, name: str, weight: int, func, description: str = ""):
        """添加启动任务

        Args:
            name: 任务名称（显示在状态标签）
            weight: 任务权重（决定进度条增量）
            func: 任务函数（将在主线程执行）
            description: 详细描述（可选）
        """
        task = StartupTask(name, weight, func, description)
        self._tasks.append(task)
        self._total_weight += weight

    def show(self):
        """显示启动画面"""
        self.window.deiconify()
        self.window.update()
        self._start_breathing_effect()

    def run_tasks(self) -> bool:
        """执行所有启动任务

        任务在主线程中顺序执行，但通过 update() 保持 UI 响应

        Returns:
            True 如果所有任务成功，否则 False
        """
        if not self._tasks:
            return True

        success = True

        for task in self._tasks:
            if self._closed:
                break

            # 更新状态显示
            self.status_label.configure(text=task.name)
            if task.description:
                self.detail_label.configure(text=task.description)
            else:
                self.detail_label.configure(text="")
            self.window.update()

            # 执行任务
            try:
                task.func()
                task.completed = True
            except Exception as e:
                task.error = str(e)
                success = False
                logger.error(f"启动任务失败 [{task.name}]: {e}")

            # 更新进度
            self._completed_weight += task.weight
            progress = (
                self._completed_weight / self._total_weight if self._total_weight > 0 else 1.0
            )
            self._animate_progress(progress)

            # 允许 UI 更新
            self.window.update()

        return success

    def _animate_progress(self, target: float):
        """平滑动画过渡到目标进度 - 性能优化版

        Args:
            target: 目标进度值 (0.0 - 1.0)
        """
        self._target_progress = target
        current = self._progress

        # 如果差距很小，直接设置
        if abs(target - current) < 0.01:
            self._progress = target
            self.progress_bar.set(target)
            self.percent_label.configure(text=f"{int(target * 100)}%")
            return

        # 使用优化的动画系统
        def update_callback(value):
            if not self._closed:
                self._progress = value
                self.progress_bar.set(value)
                self.percent_label.configure(text=f"{int(value * 100)}%")

        # 使用 150ms 快速动画，ease_out_quart 更平滑
        AnimationHelper.animate_value(
            self.window,
            current,
            target,
            AnimationHelper.DURATION_FAST,  # 150ms
            update_callback,
            easing=AnimationHelper.ease_out_quart,  # 更平滑的缓动
        )

    def _start_breathing_effect(self):
        """启动进度条呼吸效果 - 性能优化版"""
        import math

        # 预计算颜色值（缓存）
        base = ModernColors.DARK_ACCENT  # #8b5cf6
        bright = "#a78bfa"

        br = int(base.lstrip("#")[0:2], 16)
        bg = int(base.lstrip("#")[2:4], 16)
        bb = int(base.lstrip("#")[4:6], 16)

        hr = int(bright.lstrip("#")[0:2], 16)
        hg = int(bright.lstrip("#")[2:4], 16)
        hb = int(bright.lstrip("#")[4:6], 16)

        def breathe():
            if self._closed:
                return

            self._breathing_phase = (self._breathing_phase + 1) % 60

            # 计算呼吸亮度（正弦波）
            t = (math.sin(self._breathing_phase * math.pi / 30) + 1) / 2

            try:
                # 线性插值颜色
                r = int(br + (hr - br) * t)
                g = int(bg + (hg - bg) * t)
                b = int(bb + (hb - bb) * t)

                color = f"#{r:02x}{g:02x}{b:02x}"
                self.progress_bar.configure(progress_color=color)
            except Exception:
                pass

            # 降低更新频率：67ms ≈ 15fps（呼吸效果不需要 60fps）
            self._breathing_id = self.window.after(67, breathe)

        breathe()

    def update_progress(
        self, progress: float, status: str | None = None, detail: str | None = None
    ):
        """手动更新进度（用于非任务模式）

        Args:
            progress: 进度值 (0.0 - 1.0)
            status: 状态文字
            detail: 详细描述
        """
        if self._closed:
            return

        self._animate_progress(progress)

        if status:
            self.status_label.configure(text=status)
        if detail is not None:
            self.detail_label.configure(text=detail)

        self.window.update()

    def set_complete(self, message: str = "启动完成！"):
        """设置为完成状态"""
        if self._closed:
            return

        self._animate_progress(1.0)
        self.status_label.configure(text=message)
        self.detail_label.configure(text="")
        # 改变进度条颜色为成功色
        self.progress_bar.configure(progress_color=ModernColors.SUCCESS)
        self.window.update()

    def close(self, delay_ms: int = 500):
        """关闭启动画面

        Args:
            delay_ms: 关闭前延迟 (毫秒)
        """

        def do_close():
            self._closed = True

            if self._breathing_id:
                with contextlib.suppress(Exception):
                    self.window.after_cancel(self._breathing_id)

            if self._progress_animation_id:
                with contextlib.suppress(Exception):
                    self.window.after_cancel(self._progress_animation_id)

            with contextlib.suppress(Exception):
                self.window.destroy()

        if delay_ms > 0:
            self.window.after(delay_ms, do_close)
        else:
            do_close()
