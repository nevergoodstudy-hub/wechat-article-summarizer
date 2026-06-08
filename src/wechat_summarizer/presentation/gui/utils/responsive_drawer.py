"""Mobile drawer sidebar for responsive layouts."""

from __future__ import annotations

import tkinter as tk


class DrawerSidebar(tk.Frame):
    """抽屉式侧边栏（移动端）"""

    def __init__(self, parent: tk.Misc, width: int = 280, **kwargs):
        super().__init__(parent, **kwargs)

        self.drawer_width = width
        self._is_open = False
        self._animating = False

        self.colors = {"bg": "#1a1a1a", "overlay": "#000000"}

        self.configure(bg=self.colors["bg"])

        self.overlay = tk.Frame(parent, bg=self.colors["overlay"])
        self.overlay.bind("<Button-1>", lambda _event: self.close())

        self.place_forget()
        self.overlay.place_forget()

    def open(self) -> None:
        """打开抽屉"""
        if self._is_open or self._animating:
            return

        self._is_open = True
        self._animating = True

        self.overlay.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.overlay.lift()

        self._animate_open()

    def close(self) -> None:
        """关闭抽屉"""
        if not self._is_open or self._animating:
            return

        self._animating = True
        self._animate_close()

    def _animate_open(self) -> None:
        """打开动画"""
        self.place(x=-self.drawer_width, y=0, width=self.drawer_width, relheight=1.0)
        self.lift()

        steps = 15
        step_delay = 20

        def animate_step(current_step: int) -> None:
            if current_step > steps:
                self._animating = False
                return

            progress = self._ease_out(current_step / steps)
            x = int(-self.drawer_width * (1 - progress))

            self.place(x=x)

            overlay_alpha = int(128 * progress)
            self.overlay.configure(bg=f"#{overlay_alpha:02x}{overlay_alpha:02x}{overlay_alpha:02x}")

            self.after(step_delay, lambda: animate_step(current_step + 1))

        animate_step(1)

    def _animate_close(self) -> None:
        """关闭动画"""
        steps = 15
        step_delay = 20

        def animate_step(current_step: int) -> None:
            if current_step > steps:
                self._animating = False
                self._is_open = False
                self.place_forget()
                self.overlay.place_forget()
                return

            progress = self._ease_out(current_step / steps)
            x = int(-self.drawer_width * progress)

            self.place(x=x)

            self.after(step_delay, lambda: animate_step(current_step + 1))

        animate_step(1)

    def _ease_out(self, t: float) -> float:
        """ease-out缓动函数"""
        return 1 - (1 - t) ** 3

    def toggle(self) -> None:
        """切换状态"""
        if self._is_open:
            self.close()
        else:
            self.open()

    def is_open(self) -> bool:
        """是否打开状态"""
        return self._is_open


__all__ = ["DrawerSidebar"]
