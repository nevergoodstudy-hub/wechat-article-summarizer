"""Convenience functions for gradient utilities."""

from __future__ import annotations

from .gradient_manager import GradientManager


def create_gradient(colors: list[str], gradient_type: str = "linear", steps: int = 10) -> list[str]:
    """Create a gradient color list."""
    manager = GradientManager()

    if gradient_type == "radial":
        return manager.create_radial_gradient(colors, steps)
    return manager.create_linear_gradient(colors, steps)


def interpolate(color1: str, color2: str, t: float) -> str:
    """Interpolate between two colors."""
    return GradientManager.interpolate_color(color1, color2, t)


__all__ = ["create_gradient", "interpolate"]
