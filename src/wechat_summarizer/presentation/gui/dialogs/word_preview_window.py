"""Window scaffolding for Word preview dialogs."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from ..styles.colors import ModernColors
from ..styles.spacing import Spacing
from ..utils.i18n import tr

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 750


def create_preview_window(
    root: Any,
    title: str,
    *,
    center_on_parent: bool = False,
) -> ctk.CTkToplevel:
    """Create the top-level preview window."""
    preview_window = ctk.CTkToplevel(root)
    preview_window.title(title)
    preview_window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    preview_window.transient(root)

    if center_on_parent:
        preview_window.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width() - WINDOW_WIDTH) // 2
        y = root.winfo_rooty() + (root.winfo_height() - WINDOW_HEIGHT) // 2
        preview_window.geometry(f"+{x}+{y}")

    return preview_window


def add_preview_toolbar(preview_window: ctk.CTkToplevel) -> None:
    """Add the shared Word preview toolbar."""
    toolbar = ctk.CTkFrame(preview_window, height=40, fg_color="transparent")
    toolbar.pack(fill="x", padx=15, pady=(10, 5))
    ctk.CTkLabel(
        toolbar,
        text=tr("📄 Word文档预览"),
        font=ctk.CTkFont(size=16, weight="bold"),
    ).pack(side="left")
    ctk.CTkLabel(
        toolbar,
        text=tr("以下预览与最终生成的Word文档布局一致"),
        font=ctk.CTkFont(size=11),
        text_color="gray",
    ).pack(side="right")


def create_document_scroll(preview_window: ctk.CTkToplevel) -> ctk.CTkScrollableFrame:
    """Create the scrollable document surface."""
    doc_container = ctk.CTkFrame(
        preview_window,
        corner_radius=Spacing.RADIUS_SM,
        fg_color=(ModernColors.LIGHT_SURFACE_ALT, ModernColors.DARK_CARD_HOVER),
    )
    doc_container.pack(fill="both", expand=True, padx=15, pady=5)
    doc_scroll = ctk.CTkScrollableFrame(
        doc_container,
        fg_color=("white", "#1e1e1e"),
        corner_radius=0,
    )
    doc_scroll.pack(fill="both", expand=True, padx=20, pady=20)
    return doc_scroll


__all__ = [
    "WINDOW_HEIGHT",
    "WINDOW_WIDTH",
    "add_preview_toolbar",
    "create_document_scroll",
    "create_preview_window",
]
