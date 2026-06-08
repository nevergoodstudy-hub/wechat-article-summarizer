"""Gradient color generation utilities."""

from __future__ import annotations

from ..styles.colors import hex_to_rgb
from .gradient_models import GradientConfig


class GradientManager:
    """Create and query gradient color palettes."""

    MAX_STOPS = 10
    MAX_FPS = 144
    MIN_FPS = 10

    def __init__(self) -> None:
        self._active_animations: dict[int, dict[str, object]] = {}
        self._animation_id_counter = 0

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """Convert a hex color to RGB."""
        return hex_to_rgb(hex_color)

    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str:
        """Convert RGB channels to a hex color."""
        bounded = [max(0, min(255, value)) for value in (r, g, b)]
        return f"#{bounded[0]:02x}{bounded[1]:02x}{bounded[2]:02x}"

    @staticmethod
    def interpolate_color(color1: str, color2: str, t: float) -> str:
        """Interpolate between two hex colors."""
        progress = max(0.0, min(1.0, t))

        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)

        r = int(r1 + (r2 - r1) * progress)
        g = int(g1 + (g2 - g1) * progress)
        b = int(b1 + (b2 - b1) * progress)

        return GradientManager.rgb_to_hex(r, g, b)

    def create_linear_gradient(
        self,
        colors: list[str],
        steps: int = 10,
        angle: float = 0.0,
    ) -> list[str]:
        """Create a linear gradient color list."""
        _ = angle
        if len(colors) < 2:
            return colors if colors else []

        steps = max(2, min(100, steps))
        result: list[str] = []
        total_segments = len(colors) - 1
        steps_per_segment = steps // total_segments

        for i in range(total_segments):
            segment_steps = steps_per_segment
            if i == total_segments - 1:
                segment_steps = steps - len(result)
            result.extend(self._interpolate_segment(colors[i], colors[i + 1], segment_steps))

        return result

    def create_radial_gradient(
        self,
        colors: list[str],
        steps: int = 10,
        center: tuple[float, float] = (0.5, 0.5),
    ) -> list[str]:
        """Create a radial gradient color list."""
        _ = center
        return self.create_linear_gradient(colors, steps)

    def get_color_at_position(self, config: GradientConfig, position: float) -> str:
        """Return the interpolated color at a gradient position."""
        if not config.stops:
            return "#000000"

        progress = max(0.0, min(1.0, position))
        stops = sorted(config.stops, key=lambda stop: stop.position)

        if progress <= stops[0].position:
            return stops[0].color
        if progress >= stops[-1].position:
            return stops[-1].color

        for i in range(len(stops) - 1):
            start = stops[i]
            end = stops[i + 1]
            if start.position <= progress <= end.position:
                segment_length = end.position - start.position
                if segment_length == 0:
                    return start.color
                local_t = (progress - start.position) / segment_length
                return self.interpolate_color(start.color, end.color, local_t)

        return stops[-1].color

    def _interpolate_segment(self, color1: str, color2: str, steps: int) -> list[str]:
        result: list[str] = []
        for index in range(steps):
            progress = index / max(1, steps - 1) if steps > 1 else 0
            result.append(self.interpolate_color(color1, color2, progress))
        return result


__all__ = ["GradientManager"]
