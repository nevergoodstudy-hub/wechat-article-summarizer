"""Toast notification manager."""

from __future__ import annotations

from typing import Any

from .toast_item import Toast
from .toast_models import ToastType
from .toast_runtime import CTK_AVAILABLE, ctk, tk


class ToastManager:
    """Manage multiple stacked toast notifications."""

    MAX_TOASTS = 5

    def __init__(self, master: Any, position: str = "top-right", theme: str = "dark") -> None:
        self._master = master
        self._position = position
        self._theme = theme
        self._toasts: list[Toast] = []
        self._container: Any | None = None

    def _ensure_container(self) -> None:
        """Create the container lazily."""
        if self._container is not None:
            return
        if CTK_AVAILABLE and ctk is not None:
            self._container = ctk.CTkFrame(
                self._master,
                fg_color="transparent",
                width=320,
                height=1,
            )
        else:
            self._container = tk.Frame(self._master, width=320, height=1)
        self._position_container()

    def _position_container(self) -> None:
        """Place the container at the configured screen corner."""
        if self._container is None:
            return
        positions = {
            "top-right": {"relx": 1.0, "rely": 0.0, "anchor": "ne", "x": -20, "y": 20},
            "top-left": {"relx": 0.0, "rely": 0.0, "anchor": "nw", "x": 20, "y": 20},
            "bottom-right": {"relx": 1.0, "rely": 1.0, "anchor": "se", "x": -20, "y": -20},
            "bottom-left": {"relx": 0.0, "rely": 1.0, "anchor": "sw", "x": 20, "y": -20},
        }
        if placement := positions.get(self._position):
            self._container.place(**placement)

    def show(
        self,
        message: str,
        toast_type: ToastType = ToastType.INFO,
        duration: int = 3000,
    ) -> Toast:
        """Show a toast and return it."""
        self._ensure_container()
        if len(self._toasts) >= self.MAX_TOASTS:
            self._toasts[0].close()

        toast = Toast(
            self._container,
            message=message,
            toast_type=toast_type,
            duration=duration,
            on_close=lambda: self._remove_toast(toast),
            theme=self._theme,
        )
        toast.pack(fill="x", pady=(0, 8))
        self._toasts.append(toast)
        return toast

    def _remove_toast(self, toast: Toast) -> None:
        """Remove a toast from the manager."""
        if toast in self._toasts:
            self._toasts.remove(toast)

    def success(self, message: str, duration: int = 3000) -> Toast:
        """Show a success toast."""
        return self.show(message, ToastType.SUCCESS, duration)

    def error(self, message: str, duration: int = 5000) -> Toast:
        """Show an error toast."""
        return self.show(message, ToastType.ERROR, duration)

    def warning(self, message: str, duration: int = 4000) -> Toast:
        """Show a warning toast."""
        return self.show(message, ToastType.WARNING, duration)

    def info(self, message: str, duration: int = 3000) -> Toast:
        """Show an info toast."""
        return self.show(message, ToastType.INFO, duration)

    def clear_all(self) -> None:
        """Close every active toast."""
        for toast in self._toasts[:]:
            toast.close()


__all__ = ["ToastManager"]
