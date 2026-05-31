"""
展示层

包含用户交互界面：
- gui: 图形界面 (CustomTkinter)
- cli: 命令行界面 (Click + Rich)
"""

from .cli import run_cli


def run_gui() -> None:
    """Launch the GUI without importing GUI extras during package import."""
    from .gui import run_gui as _run_gui

    _run_gui()


__all__ = ["run_cli", "run_gui"]
