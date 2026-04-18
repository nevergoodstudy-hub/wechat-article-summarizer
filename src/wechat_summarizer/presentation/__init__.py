"""
展示层

包含用户交互界面：
- gui: 图形界面 (CustomTkinter)
- cli: 命令行界面 (Click + Rich)
"""

__all__ = ["run_cli", "run_gui"]


def run_cli() -> None:
    """Lazily dispatch to the CLI entrypoint."""
    from .cli import run_cli as _run_cli

    _run_cli()


def run_gui(*, raise_on_error: bool = False) -> None:
    """Lazily dispatch to the GUI entrypoint."""
    from .gui import run_gui as _run_gui

    _run_gui(raise_on_error=raise_on_error)
