"""Home dashboard page."""

from __future__ import annotations

from typing import Any

from ..frames import (
    HomeActionCardsFrame,
    HomeInfoRowFrame,
    HomeTipBarFrame,
    HomeWelcomeFrame,
)

_ctk_available = True
try:
    import customtkinter as ctk
except ImportError:
    _ctk_available = False


class HomePage(ctk.CTkFrame):
    """Dashboard page that coordinates reusable home frames."""

    PAGE_SINGLE = "single"
    PAGE_BATCH = "batch"
    PAGE_HISTORY = "history"
    PAGE_SETTINGS = "settings"

    def __init__(self, master: Any, gui: Any, **kwargs: Any) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.gui = gui
        self._unsubscribe_navigate = None
        if hasattr(self.gui, "event_bus"):
            self._unsubscribe_navigate = self.gui.event_bus.subscribe(
                "navigate", self._on_navigate_event
            )

        self._build()

    def _build(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)
        self._scroll.grid_columnconfigure(0, weight=1)

        pages = {
            "single": self.PAGE_SINGLE,
            "batch": self.PAGE_BATCH,
            "history": self.PAGE_HISTORY,
            "settings": self.PAGE_SETTINGS,
        }

        self.welcome_frame = HomeWelcomeFrame(
            self._scroll,
            gui=self.gui,
            page_single=self.PAGE_SINGLE,
        )
        self.welcome_frame.pack(fill="x", pady=(0, 20))

        self.action_cards_frame = HomeActionCardsFrame(
            self._scroll,
            gui=self.gui,
            pages=pages,
        )
        self.action_cards_frame.pack(fill="x", pady=(0, 15))

        self.info_row_frame = HomeInfoRowFrame(
            self._scroll,
            gui=self.gui,
            pages=pages,
        )
        self.info_row_frame.pack(fill="x", pady=(0, 10))

        self.tip_bar_frame = HomeTipBarFrame(self._scroll, gui=self.gui)
        self.tip_bar_frame.pack(fill="x", padx=8, pady=(5, 10))

    def refresh_recent(self) -> None:
        """Refresh recent records after article processing completes."""
        self.info_row_frame.refresh_recent()

    def _on_navigate_event(self, *, from_page: str, to_page: str) -> None:
        """Reserve dashboard navigation hook for future metrics."""
        _ = from_page
        _ = to_page
