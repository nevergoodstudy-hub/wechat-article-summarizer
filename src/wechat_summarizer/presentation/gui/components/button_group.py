"""Button group component."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any

from .button_compat import CTK_AVAILABLE, ctk
from .button_modern import ModernButton


class ButtonGroup:
    """按钮组"""

    def __init__(self, master: Any, orientation: str = "horizontal"):
        self._orientation = orientation

        if CTK_AVAILABLE and ctk is not None:
            self._frame = ctk.CTkFrame(master, fg_color="transparent")
        else:
            self._frame = tk.Frame(master)

        self._buttons: list[ModernButton] = []

    def add_button(
        self,
        text: str,
        command: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> ModernButton:
        """添加按钮到组"""
        button = ModernButton(self._frame, text=text, command=command, **kwargs)

        if self._orientation == "horizontal":
            button.pack(side="left", padx=(0 if len(self._buttons) == 0 else 8, 0))
        else:
            button.pack(pady=(0 if len(self._buttons) == 0 else 8, 0))

        self._buttons.append(button)
        return button

    def pack(self, **kwargs: Any) -> None:
        """打包按钮组"""
        self._frame.pack(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        """网格布局按钮组"""
        self._frame.grid(**kwargs)


__all__ = ["ButtonGroup"]
