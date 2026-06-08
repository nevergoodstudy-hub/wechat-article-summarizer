"""Glass button component."""

from __future__ import annotations

from .glass_compat import CTK_AVAILABLE, ctk, tk
from .glass_models import resolve_glass_theme


class GlassButton(ctk.CTkButton if CTK_AVAILABLE else tk.Button):  # type: ignore[misc]
    """Button with glass-styled theme colors."""

    def __init__(
        self,
        master,
        text: str = "",
        command=None,
        theme: str = "dark",
        **kwargs,
    ) -> None:
        colors = resolve_glass_theme(theme)

        if CTK_AVAILABLE:
            super().__init__(
                master,
                text=text,
                command=command,
                fg_color=colors.accent,
                hover_color=colors.accent_hover,
                text_color=colors.text,
                corner_radius=12,
                border_width=1,
                border_color=colors.border,
                font=("Inter", 14),
                **kwargs,
            )
        else:
            super().__init__(
                master,
                text=text,
                command=command,
                bg=colors.accent,
                fg=colors.text,
                activebackground=colors.accent_hover,
                font=("Arial", 14),
                relief="flat",
                **kwargs,
            )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event) -> None:
        """Handle hover enter."""
        _ = event

    def _on_leave(self, event) -> None:
        """Handle hover leave."""
        _ = event


__all__ = ["GlassButton"]
