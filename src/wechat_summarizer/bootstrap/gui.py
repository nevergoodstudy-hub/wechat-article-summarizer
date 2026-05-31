"""GUI composition root."""

from __future__ import annotations

from ..infrastructure.config import get_container, get_settings
from ..presentation.gui.app import run_gui as run_gui_with_dependencies


def run_gui() -> None:
    """Launch the GUI with infrastructure dependencies assembled."""
    run_gui_with_dependencies(container=get_container(), settings=get_settings())
