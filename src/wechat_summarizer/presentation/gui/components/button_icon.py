"""Icon button component."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .button_compat import CTK_AVAILABLE
from .button_models import ButtonSize, ButtonVariant, get_icon_button_size
from .button_modern import ModernButton


class IconButton(ModernButton):
    """图标按钮"""

    def __init__(
        self,
        master: Any,
        icon: Any,
        command: Callable[[], None] | None = None,
        variant: ButtonVariant = ButtonVariant.GHOST,
        size: ButtonSize = ButtonSize.MEDIUM,
        theme: str = "dark",
        **kwargs: Any,
    ):
        size_value = get_icon_button_size(size)
        super().__init__(
            master,
            text="",
            command=command,
            variant=variant,
            size=size,
            icon=icon,
            theme=theme,
            width=size_value,
            **kwargs,
        )

        if CTK_AVAILABLE:
            self.configure(corner_radius=size_value // 2)


__all__ = ["IconButton"]
