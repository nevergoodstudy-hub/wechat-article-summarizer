"""Compatibility exports for gradient color utilities."""

from __future__ import annotations

from .gradient_animator import GradientAnimator
from .gradient_facade import create_gradient, interpolate
from .gradient_manager import GradientManager
from .gradient_models import EasingFunction, GradientConfig, GradientStop, GradientType

__all__ = [
    "EasingFunction",
    "GradientAnimator",
    "GradientConfig",
    "GradientManager",
    "GradientStop",
    "GradientType",
    "create_gradient",
    "interpolate",
]
