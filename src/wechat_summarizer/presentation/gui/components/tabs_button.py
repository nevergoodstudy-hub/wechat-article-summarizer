"""Tab button rendering mixin."""

from __future__ import annotations

import tkinter as tk
from typing import Any

from ..styles.typography import TextStyles, get_text_style
from .tabs_compat import CTK_AVAILABLE, ctk
from .tabs_models import TabItem


class TabsButtonMixin:
    """Create tab button widgets and hover behavior."""

    _active_tab_id: str | None
    _colors: dict[str, str]
    _draggable: bool

    def _create_tab_button(self: Any, tab: TabItem) -> None:
        btn_frame = tk.Frame(self._tabs_container, bg=self._colors["tab_bg"])
        btn_frame.pack(side="left", padx=2, pady=(4, 0))

        label_btn = self._create_label_button(btn_frame, tab)
        label_btn.pack(side="left", padx=(8, 0 if tab.closable else 8))

        close_btn = self._create_close_button(btn_frame, tab)
        if close_btn is not None:
            close_btn.pack(side="left", padx=(4, 8))

        if self._draggable:
            label_btn.bind("<ButtonPress-1>", lambda e, tid=tab.id: self._on_drag_start(e, tid))
            label_btn.bind("<B1-Motion>", self._on_drag_motion)
            label_btn.bind("<ButtonRelease-1>", self._on_drag_end)

        self._tab_buttons[tab.id] = {
            "frame": btn_frame,
            "label": label_btn,
            "close": close_btn,
        }

    def _create_label_button(self: Any, btn_frame: tk.Frame, tab: TabItem) -> Any:
        if CTK_AVAILABLE and ctk is not None:
            return ctk.CTkButton(
                btn_frame,
                text=tab.label,
                fg_color="transparent",
                hover_color=self._colors["tab_hover_bg"],
                text_color=self._colors["text_secondary"],
                corner_radius=6,
                height=32,
                font=get_text_style(TextStyles.BODY),
                command=lambda: self.select_tab(tab.id),
            )

        label_btn = tk.Button(
            btn_frame,
            text=tab.label,
            bg=self._fallback_label_background(),
            fg=self._colors["text_secondary"],
            relief="flat",
            font=get_text_style(TextStyles.BODY),
            command=lambda: self.select_tab(tab.id),
            cursor="hand2",
        )

        def on_label_enter(_event: tk.Event[tk.Misc], button: tk.Button = label_btn) -> None:
            button.configure(bg=self._colors["tab_hover_bg"])

        def on_label_leave(
            _event: tk.Event[tk.Misc],
            button: tk.Button = label_btn,
            tab_id: str = tab.id,
        ) -> None:
            button.configure(
                bg=self._colors["tab_active_bg"]
                if tab_id == self._active_tab_id
                else self._colors["tab_bar_bg"]
            )

        label_btn.bind("<Enter>", on_label_enter)
        label_btn.bind("<Leave>", on_label_leave)
        return label_btn

    def _fallback_label_background(self: Any) -> str:
        if self._colors["tab_bg"] != "transparent":
            return str(self._colors["tab_bg"])
        return str(self._colors["tab_bar_bg"])

    def _create_close_button(self: Any, btn_frame: tk.Frame, tab: TabItem) -> Any | None:
        if not tab.closable:
            return None

        if CTK_AVAILABLE and ctk is not None:
            return ctk.CTkButton(
                btn_frame,
                text="×",
                width=20,
                height=20,
                fg_color="transparent",
                hover_color=self._colors["close_hover"],
                text_color=self._colors["text_secondary"],
                corner_radius=10,
                font=("Arial", 12),
                command=lambda: self.close_tab(tab.id),
            )

        close_btn = tk.Button(
            btn_frame,
            text="×",
            width=2,
            bg=self._colors["tab_bar_bg"],
            fg=self._colors["text_secondary"],
            relief="flat",
            font=("Arial", 10),
            command=lambda: self.close_tab(tab.id),
            cursor="hand2",
        )

        def on_close_enter(_event: tk.Event[tk.Misc], button: tk.Button = close_btn) -> None:
            button.configure(bg=self._colors["close_hover"], fg="#FFFFFF")

        def on_close_leave(_event: tk.Event[tk.Misc], button: tk.Button = close_btn) -> None:
            button.configure(bg=self._colors["tab_bar_bg"], fg=self._colors["text_secondary"])

        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
        return close_btn


__all__ = ["TabsButtonMixin"]
