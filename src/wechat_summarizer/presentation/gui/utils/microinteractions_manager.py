"""Microinteraction registration and cleanup manager."""

from __future__ import annotations

import tkinter as tk
from typing import Protocol

from .microinteractions_feedback import HoverEffect, RippleEffect, ScaleEffect
from .microinteractions_focus import FocusRing
from .microinteractions_motion import PulseEffect


class DestroyableEffect(Protocol):
    def destroy(self) -> None:
        """Release widget bindings or scheduled callbacks."""


class MicroInteractions:
    """微交互管理器"""

    _effects: dict[int, list[DestroyableEffect]] = {}

    @classmethod
    def add_ripple(
        cls,
        widget: tk.Widget,
        color: str = "#ffffff",
        duration: int = 400,
    ) -> RippleEffect:
        effect = RippleEffect(widget, color, duration)
        cls._register(widget, effect)
        return effect

    @classmethod
    def add_scale(
        cls,
        widget: tk.Widget,
        scale_down: float = 0.95,
        duration: int = 100,
    ) -> ScaleEffect:
        effect = ScaleEffect(widget, scale_down, duration)
        cls._register(widget, effect)
        return effect

    @classmethod
    def add_hover(
        cls,
        widget: tk.Widget,
        hover_bg: str | None = None,
        normal_bg: str | None = None,
        lift_pixels: int = 2,
    ) -> HoverEffect:
        effect = HoverEffect(widget, hover_bg, normal_bg, lift_pixels)
        cls._register(widget, effect)
        return effect

    @classmethod
    def add_pulse(
        cls,
        widget: tk.Widget,
        color1: str = "#3b82f6",
        color2: str = "#60a5fa",
    ) -> PulseEffect:
        effect = PulseEffect(widget, color1, color2)
        cls._register(widget, effect)
        return effect

    @classmethod
    def add_focus_ring(
        cls,
        widget: tk.Widget,
        color: str = "#3b82f6",
        width: int = 2,
    ) -> FocusRing:
        effect = FocusRing(widget, color, width)
        cls._register(widget, effect)
        return effect

    @classmethod
    def _register(cls, widget: tk.Widget, effect: DestroyableEffect) -> None:
        widget_id = id(widget)
        if widget_id not in cls._effects:
            cls._effects[widget_id] = []
        cls._effects[widget_id].append(effect)

    @classmethod
    def remove_all(cls, widget: tk.Widget) -> None:
        widget_id = id(widget)
        if widget_id in cls._effects:
            for effect in cls._effects[widget_id]:
                effect.destroy()
            del cls._effects[widget_id]

    @classmethod
    def cleanup(cls) -> None:
        for _widget_id, effects in list(cls._effects.items()):
            for effect in effects:
                effect.destroy()
        cls._effects.clear()


__all__ = [
    "DestroyableEffect",
    "MicroInteractions",
]
