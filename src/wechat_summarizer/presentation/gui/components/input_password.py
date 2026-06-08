"""Password input widget."""

from __future__ import annotations

from typing import Any

from .input_compat import CTK_AVAILABLE
from .input_modern import ModernInput


class PasswordInput(ModernInput):
    """Password input with a visibility toggle API."""

    def __init__(self, master: Any, label: str = "密码", theme: str = "dark", **kwargs: Any):
        self._show_password = False
        super().__init__(
            master,
            label=label,
            theme=theme,
            show="*" if not CTK_AVAILABLE else None,
            **kwargs,
        )
        if CTK_AVAILABLE:
            self.configure(show="*")

    def toggle_visibility(self) -> None:
        self._show_password = not self._show_password
        self.configure(show="" if self._show_password else "*")
