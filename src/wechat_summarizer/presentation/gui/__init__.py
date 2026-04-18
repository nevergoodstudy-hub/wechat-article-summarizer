"""GUI 展示层。"""

from __future__ import annotations

from typing import Any

__all__ = ["MainWindow", "WechatSummarizerGUI", "run_gui"]


def run_gui(*, raise_on_error: bool = False) -> None:
    """Lazily launch the GUI entrypoint."""
    from .app import run_gui as _run_gui

    _run_gui(raise_on_error=raise_on_error)


def __getattr__(name: str) -> Any:
    """Load heavy GUI exports on demand."""
    if name == "WechatSummarizerGUI":
        from .app import WechatSummarizerGUI

        return WechatSummarizerGUI
    if name == "MainWindow":
        from .main_window import MainWindow

        return MainWindow
    raise AttributeError(name)
