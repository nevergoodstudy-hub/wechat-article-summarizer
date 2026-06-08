"""Compatibility entrypoint for GUI microinteraction effects."""

from __future__ import annotations

from .microinteractions_feedback import HoverEffect, RippleEffect, ScaleEffect
from .microinteractions_focus import FocusRing
from .microinteractions_loading import SkeletonLoader, Spinner
from .microinteractions_manager import MicroInteractions
from .microinteractions_motion import CollapseExpand, PulseEffect

__all__ = [
    "CollapseExpand",
    "FocusRing",
    "HoverEffect",
    "MicroInteractions",
    "PulseEffect",
    "RippleEffect",
    "ScaleEffect",
    "SkeletonLoader",
    "Spinner",
]


if __name__ == "__main__":
    from .microinteractions_demo import run_microinteractions_demo

    run_microinteractions_demo()
