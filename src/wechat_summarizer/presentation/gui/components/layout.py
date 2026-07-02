"""Shared layout primitives for the desktop GUI."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing

try:
    import customtkinter as ctk

    _CTK_AVAILABLE = True
except ImportError:
    _CTK_AVAILABLE = False
    ctk = None


@dataclass(frozen=True)
class MetricSpec:
    """Small status metric shown in a compact tile."""

    label: str
    value: str
    tone: str = ModernColors.INFO


def muted_text_color() -> tuple[str, str]:
    """Return the standard muted text color pair."""
    return (ModernColors.LIGHT_TEXT_SECONDARY, ModernColors.DARK_TEXT_SECONDARY)


def normal_text_color() -> tuple[str, str]:
    """Return the standard foreground text color pair."""
    return (ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT)


def panel_color() -> tuple[str, str]:
    """Return the standard panel background color pair."""
    return (ModernColors.LIGHT_CARD, ModernColors.DARK_CARD)


def inset_color() -> tuple[str, str]:
    """Return the standard inset background color pair."""
    return (ModernColors.LIGHT_INSET, ModernColors.DARK_INSET)


def border_color() -> tuple[str, str]:
    """Return the standard border color pair."""
    return (ModernColors.LIGHT_BORDER, ModernColors.DARK_BORDER)


def workspace_bg_color() -> tuple[str, str]:
    """Return the app workspace background color pair."""
    return (ModernColors.LIGHT_BG, ModernColors.DARK_BG)


def surface_alt_color() -> tuple[str, str]:
    """Return the alternate surface color pair."""
    return (ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_SURFACE_ALT)


def subtle_hover_color() -> tuple[str, str]:
    """Return the standard subtle hover color pair."""
    return (ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE)


class PageHeader(ctk.CTkFrame if _CTK_AVAILABLE else object):  # type: ignore[misc]
    """Consistent page heading with optional right-side action area."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        eyebrow: str,
        title: str,
        subtitle: str,
        accent: str = ModernColors.INFO,
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.actions = ctk.CTkFrame(self, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        title_stack = ctk.CTkFrame(self, fg_color="transparent")
        title_stack.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            title_stack,
            text=eyebrow,
            font=gui._get_font(11, "bold"),
            text_color=accent,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_stack,
            text=title,
            font=gui._get_font(24, "bold"),
            text_color=normal_text_color(),
            anchor="w",
        ).pack(anchor="w", pady=(2, 2))
        ctk.CTkLabel(
            title_stack,
            text=subtitle,
            font=gui._get_font(13),
            text_color=muted_text_color(),
            anchor="w",
        ).pack(anchor="w")

        self.actions.grid(row=0, column=1, sticky="e", padx=(20, 0))


class SurfacePanel(ctk.CTkFrame if _CTK_AVAILABLE else object):  # type: ignore[misc]
    """A reusable panel with a compact header and body container."""

    def __init__(
        self,
        master: Any,
        *,
        gui: Any,
        title: str | None = None,
        subtitle: str | None = None,
        accent: str = ModernColors.INFO,
        compact: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            master,
            fg_color=panel_color(),
            corner_radius=Spacing.RADIUS_LG,
            border_width=1,
            border_color=border_color(),
            **kwargs,
        )
        pad_x = 16 if compact else 20
        pad_y = 12 if compact else 16

        if title or subtitle:
            header = ctk.CTkFrame(self, fg_color="transparent")
            header.pack(fill="x", padx=pad_x, pady=(pad_y, 10))
            header.grid_columnconfigure(1, weight=1)

            ctk.CTkFrame(
                header,
                width=4,
                height=34 if not compact else 28,
                corner_radius=2,
                fg_color=accent,
            ).grid(row=0, column=0, sticky="nsw", padx=(0, 10))

            text_stack = ctk.CTkFrame(header, fg_color="transparent")
            text_stack.grid(row=0, column=1, sticky="ew")
            if title:
                ctk.CTkLabel(
                    text_stack,
                    text=title,
                    font=gui._get_font(14 if compact else 15, "bold"),
                    text_color=normal_text_color(),
                    anchor="w",
                ).pack(anchor="w")
            if subtitle:
                ctk.CTkLabel(
                    text_stack,
                    text=subtitle,
                    font=gui._get_font(11),
                    text_color=muted_text_color(),
                    anchor="w",
                ).pack(anchor="w", pady=(2, 0))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=pad_x, pady=(0, pad_y))


def create_metric_tile(master: Any, *, gui: Any, spec: MetricSpec) -> Any:
    """Create a compact metric tile and return it."""
    tile = ctk.CTkFrame(
        master,
        fg_color=surface_alt_color(),
        corner_radius=Spacing.RADIUS_MD,
        border_width=1,
        border_color=border_color(),
    )
    ctk.CTkLabel(
        tile,
        text=spec.label,
        font=gui._get_font(11),
        text_color=muted_text_color(),
        anchor="w",
    ).pack(anchor="w", padx=12, pady=(10, 1))
    ctk.CTkLabel(
        tile,
        text=spec.value,
        font=gui._get_font(18, "bold"),
        text_color=spec.tone,
        anchor="w",
    ).pack(anchor="w", padx=12, pady=(0, 10))
    return tile


def create_badge(
    master: Any,
    *,
    gui: Any,
    text: str,
    tone: str = ModernColors.INFO,
    width: int | None = None,
) -> Any:
    """Create a small label badge."""
    label = ctk.CTkLabel(
        master,
        text=text,
        width=width or 0,
        height=24,
        corner_radius=Spacing.RADIUS_MD,
        fg_color=surface_alt_color(),
        text_color=tone,
        font=gui._get_font(11, "bold"),
        padx=10,
    )
    return label


def create_status_pill(
    master: Any,
    *,
    gui: Any,
    label: str,
    value: str,
    tone: str = ModernColors.SUCCESS,
) -> Any:
    """Create an inline status pill for shell and dashboard summaries."""
    pill = ctk.CTkFrame(
        master,
        fg_color=surface_alt_color(),
        corner_radius=Spacing.RADIUS_MD,
        border_width=1,
        border_color=border_color(),
    )
    ctk.CTkLabel(
        pill,
        text=label,
        font=gui._get_font(11),
        text_color=muted_text_color(),
    ).pack(side="left", padx=(10, 4), pady=5)
    ctk.CTkLabel(
        pill,
        text=value,
        font=gui._get_font(11, "bold"),
        text_color=tone,
    ).pack(side="left", padx=(0, 10), pady=5)
    return pill


def create_divider(master: Any) -> Any:
    """Create a thin divider line."""
    return ctk.CTkFrame(master, height=1, fg_color=border_color(), corner_radius=0)


def create_empty_state(
    master: Any,
    *,
    gui: Any,
    title: str,
    detail: str,
    command: Callable[[], None] | None = None,
    action_text: str | None = None,
) -> Any:
    """Create a centered empty state block."""
    frame = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(
        frame,
        text=title,
        font=gui._get_font(15, "bold"),
        text_color=normal_text_color(),
    ).pack(pady=(6, 3))
    ctk.CTkLabel(
        frame,
        text=detail,
        font=gui._get_font(12),
        text_color=muted_text_color(),
        justify="center",
    ).pack(pady=(0, 10))
    if command and action_text:
        ctk.CTkButton(
            frame,
            text=action_text,
            height=32,
            corner_radius=Spacing.RADIUS_MD,
            fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
            hover_color=(ModernColors.LIGHT_ACCENT_HOVER, ModernColors.DARK_ACCENT_HOVER),
            command=command,
        ).pack()
    return frame
