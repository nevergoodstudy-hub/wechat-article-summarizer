"""GUI展示层"""

from .app import WechatSummarizerGUI
from .app import run_gui as run_gui_with_dependencies
from .main_window import MainWindow


def run_gui() -> None:
    """Launch the GUI through the application composition root."""
    from ...bootstrap.gui import run_gui as run_bootstrapped_gui

    run_bootstrapped_gui()


__all__ = ["MainWindow", "WechatSummarizerGUI", "run_gui", "run_gui_with_dependencies"]
