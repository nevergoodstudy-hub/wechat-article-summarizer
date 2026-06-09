"""Optional runtime dependencies for the graph viewer."""

from __future__ import annotations

from typing import Any

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False
    ctk = None  # type: ignore[assignment]


def require_ctk() -> Any:
    """Return customtkinter or raise the legacy import hint."""
    if not _ctk_available or ctk is None:
        raise ImportError("需要安装 customtkinter: pip install customtkinter")
    return ctk


__all__ = ["_ctk_available", "ctk", "require_ctk"]
