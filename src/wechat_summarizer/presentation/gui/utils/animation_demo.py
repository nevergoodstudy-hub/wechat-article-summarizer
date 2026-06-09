"""Manual demo for GUI animation utilities."""

from __future__ import annotations

import tkinter as tk

from .animation_engine import AnimationEngine
from .animation_models import EasingType, Tween
from .i18n import tr


def run_animation_demo() -> None:
    """Run the manual animation engine demo."""
    root = tk.Tk()
    root.title(tr("动画引擎测试"))
    root.geometry("800x600")
    root.configure(bg="#121212")

    engine = AnimationEngine(root)
    fps_label = tk.Label(
        root,
        text=tr("FPS: 0"),
        bg="#121212",
        fg="#e5e5e5",
        font=("Segoe UI", 12),
    )
    fps_label.pack(pady=10)

    def update_fps() -> None:
        fps_label.config(
            text=tr("FPS: {fps} | 活动动画: {count}").format(
                fps=engine.get_fps(),
                count=engine.get_active_count(),
            )
        )
        root.after(500, update_fps)

    update_fps()

    canvas = tk.Canvas(root, width=600, height=400, bg="#1e1e1e", highlightthickness=0)
    canvas.pack(pady=20)
    ball = canvas.create_oval(50, 50, 100, 100, fill="#3b82f6", outline="")

    class BallAnimator:
        def __init__(self) -> None:
            self.x = 50
            self.y = 50

        def update(self) -> None:
            canvas.coords(ball, self.x, self.y, self.x + 50, self.y + 50)

    ball_anim = BallAnimator()

    def animate_ball() -> None:
        tween1 = Tween(
            target=ball_anim,
            property_name="x",
            start_value=50,
            end_value=500,
            duration=500,
            easing=EasingType.EASE_OUT_ELASTIC,
            on_update=lambda _value: ball_anim.update(),
        )
        tween2 = Tween(
            target=ball_anim,
            property_name="y",
            start_value=50,
            end_value=300,
            duration=500,
            easing=EasingType.EASE_OUT_BOUNCE,
            on_update=lambda _value: ball_anim.update(),
        )
        tween3 = Tween(
            target=ball_anim,
            property_name="x",
            start_value=500,
            end_value=50,
            duration=500,
            easing=EasingType.EASE_IN_OUT_CUBIC,
            on_update=lambda _value: ball_anim.update(),
        )
        tween4 = Tween(
            target=ball_anim,
            property_name="y",
            start_value=300,
            end_value=50,
            duration=500,
            easing=EasingType.EASE_IN_OUT_CUBIC,
            on_update=lambda _value: ball_anim.update(),
        )
        engine.sequence([tween1, tween2, tween3, tween4], on_complete=animate_ball)

    tk.Button(
        root,
        text=tr("开始动画"),
        command=animate_ball,
        bg="#3b82f6",
        fg="#ffffff",
        font=("Segoe UI", 12),
        relief=tk.FLAT,
        padx=20,
        pady=10,
    ).pack(pady=10)

    tk.Button(
        root,
        text=tr("停止所有"),
        command=engine.stop_all,
        bg="#ef4444",
        fg="#ffffff",
        font=("Segoe UI", 12),
        relief=tk.FLAT,
        padx=20,
        pady=10,
    ).pack(pady=5)

    root.mainloop()


__all__ = ["run_animation_demo"]
