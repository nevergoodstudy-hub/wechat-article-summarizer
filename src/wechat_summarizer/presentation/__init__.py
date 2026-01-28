"""
展示层

包含用户交互界面：
- gui: 图形界面 (CustomTkinter)
- cli: 命令行界面 (Click + Rich)
"""

from .cli import run_cli
from .gui import run_gui

__all__ = ["run_gui", "run_cli"]
