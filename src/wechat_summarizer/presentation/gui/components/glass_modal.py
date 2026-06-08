"""Glass modal component."""

from __future__ import annotations

from .glass_compat import tk
from .glass_frame import LiquidGlassFrame


class GlassModal(tk.Toplevel):
    """Modal dialog with a glass background frame."""

    def __init__(
        self,
        master,
        title: str = "",
        width: int = 400,
        height: int = 300,
        theme: str = "dark",
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)

        self.title(title)
        self.geometry(f"{width}x{height}")
        self.transient(master)
        self.grab_set()

        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")

        self._glass_frame = LiquidGlassFrame(
            self,
            width=width,
            height=height,
            opacity=0.95,
            theme=theme,
        )
        self._glass_frame.pack(fill="both", expand=True)
        self.bind("<Escape>", lambda _event: self.destroy())


__all__ = ["GlassModal"]
