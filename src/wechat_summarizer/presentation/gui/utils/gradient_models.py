"""Models for gradient color utilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GradientType(Enum):
    """Supported gradient types."""

    LINEAR = "linear"
    RADIAL = "radial"
    CONIC = "conic"


class EasingFunction(Enum):
    """Animation easing function names."""

    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


@dataclass
class GradientStop:
    """A gradient color stop."""

    color: str
    position: float

    def __post_init__(self) -> None:
        self.position = max(0.0, min(1.0, self.position))


@dataclass
class GradientConfig:
    """Gradient generation configuration."""

    type: GradientType = GradientType.LINEAR
    stops: list[GradientStop] | None = None
    angle: float = 0.0
    center: tuple[float, float] = (0.5, 0.5)

    def __post_init__(self) -> None:
        if self.stops is None:
            self.stops = []
        self.angle %= 360


__all__ = [
    "EasingFunction",
    "GradientConfig",
    "GradientStop",
    "GradientType",
]
