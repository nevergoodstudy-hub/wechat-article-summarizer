"""Glass card component."""

from __future__ import annotations

from .glass_compat import CTK_AVAILABLE, ctk, tk
from .glass_frame import LiquidGlassFrame
from .glass_models import resolve_glass_theme


class GlassCard(LiquidGlassFrame):
    """Card based on the liquid glass material."""

    def __init__(
        self,
        master,
        width: int = 300,
        height: int = 200,
        title: str | None = None,
        theme: str = "dark",
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            width=width,
            height=height,
            opacity=0.9,
            blur_radius=15,
            border_glow=True,
            theme=theme,
            corner_radius=16,
            **kwargs,
        )

        self._content_frame: tk.Widget | None = None
        self._title_label: tk.Widget | None = None

        if title:
            self._create_title(title)

    def _create_title(self, title: str) -> None:
        colors = resolve_glass_theme(self._theme)

        if CTK_AVAILABLE:
            self._title_label = ctk.CTkLabel(
                self,
                text=title,
                font=("Inter", 20, "bold"),
                text_color=colors.text,
            )
        else:
            self._title_label = tk.Label(
                self,
                text=title,
                font=("Arial", 20, "bold"),
                fg=colors.text,
                bg=self._base_color,
            )

        if self._title_label is not None:
            self._title_label.pack(pady=(20, 10), padx=20, anchor="w")

    def add_content(self, widget) -> None:
        """Add a child widget to the card content area."""
        if self._content_frame is None:
            if CTK_AVAILABLE:
                self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
            else:
                self._content_frame = tk.Frame(self, bg=self._base_color)
            self._content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        widget.pack(in_=self._content_frame, fill="both", expand=True)


__all__ = ["GlassCard"]
