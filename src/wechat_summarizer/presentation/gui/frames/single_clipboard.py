"""Clipboard suggestion frame for the single-article page."""

from __future__ import annotations

from collections.abc import Callable

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr

try:
    import customtkinter as ctk
except ImportError:  # pragma: no cover - GUI dependency is optional at runtime
    ctk = None  # type: ignore[assignment]


class SingleClipboardBannerFrame(ctk.CTkFrame):
    """Banner shown when a WeChat link is detected in the clipboard."""

    def __init__(
        self,
        master,
        *,
        url: str,
        on_apply: Callable[[str], None],
        on_dismiss: Callable[[], None],
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT),
            corner_radius=Spacing.RADIUS_MD,
            **kwargs,
        )
        self.url = url
        self._on_apply = on_apply
        self._on_dismiss = on_dismiss
        self._build()

    @staticmethod
    def format_url(url: str, *, max_length: int = 50) -> str:
        """Return a compact URL preview for the banner label."""
        if len(url) <= max_length:
            return url
        return url[: max_length - 2] + "…"

    def _build(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=8)

        ctk.CTkLabel(
            inner,
            text=tr(f"📋 检测到剪贴板链接: {self.format_url(self.url)}"),
            font=ctk.CTkFont(size=12),
            text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            inner,
            text=tr("粘贴使用"),
            font=ctk.CTkFont(size=11, weight="bold"),
            width=80,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(ModernColors.LIGHT_ACCENT_HOVER, ModernColors.DARK_ACCENT_HOVER),
            command=lambda: self._on_apply(self.url),
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            inner,
            text="✕",
            width=28,
            height=28,
            corner_radius=Spacing.RADIUS_SM,
            fg_color="transparent",
            text_color=(ModernColors.LIGHT_TEXT_MUTED, ModernColors.DARK_TEXT_MUTED),
            hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
            command=self._on_dismiss,
        ).pack(side="right")


__all__ = ["SingleClipboardBannerFrame"]
