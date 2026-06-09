"""Compatibility entrypoint for page transitions."""

from __future__ import annotations

from .transition_easing import Easing
from .transition_models import EasingFunction, TransitionConfig, TransitionType
from .transition_page import PageTransition
from .transition_router import PageRouter

__all__ = [
    "Easing",
    "EasingFunction",
    "PageRouter",
    "PageTransition",
    "TransitionConfig",
    "TransitionType",
]


if __name__ == "__main__":
    from .transition_demo import run_demo

    run_demo()
