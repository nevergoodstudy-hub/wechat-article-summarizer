"""Rendering helpers for built-in SVG path icons."""

from __future__ import annotations

import contextlib
from io import BytesIO
from typing import Any

from .icons_parser import SVGPathParser
from .icons_runtime import CAIROSVG_AVAILABLE, PIL_AVAILABLE, Image, ImageDraw, cairosvg


class IconRenderer:
    """Render SVG path data to image objects."""

    @staticmethod
    def validate_color(color: str) -> bool:
        """验证颜色格式"""
        if not isinstance(color, str):
            return False

        import re

        pattern = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
        return bool(re.match(pattern, color))

    @staticmethod
    def parse_color(color: str) -> tuple[int, int, int, int]:
        """解析颜色为RGBA"""
        try:
            if color.startswith("#"):
                hex_color = color[1:]
                if len(hex_color) == 3:
                    hex_color = "".join([character * 2 for character in hex_color])
                red = int(hex_color[0:2], 16)
                green = int(hex_color[2:4], 16)
                blue = int(hex_color[4:6], 16)
                return (red, green, blue, 255)
        except (ValueError, IndexError):
            pass
        return (255, 255, 255, 255)

    def render(self, path_data: str, size: int, color: str) -> Any | None:
        """Render path data with cairosvg when available, otherwise PIL."""
        if not PIL_AVAILABLE:
            return None
        if CAIROSVG_AVAILABLE:
            return self._render_with_cairosvg(path_data, size, color)
        return self.render_with_pil(path_data, size, color)

    def _render_with_cairosvg(self, path_data: str, size: int, color: str) -> Any | None:
        try:
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
            <svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">
                <path d="{path_data}" fill="{color}"/>
            </svg>'''
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode("utf-8"),
                output_width=size,
                output_height=size,
            )
            return Image.open(BytesIO(png_data))
        except Exception:
            return self.render_with_pil(path_data, size, color)

    def render_with_pil(self, path_data: str, size: int, color: str) -> Any | None:
        """使用PIL手动渲染SVG路径"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        scale = size / 24.0

        try:
            commands = SVGPathParser.parse(path_data, scale=scale)
        except Exception:
            return self.create_fallback_icon(size, color)

        fill_color = self.parse_color(color)
        polygon_points: list[tuple[float, float]] = []
        current_pos: tuple[float, float] | None = None

        for cmd, points in commands:
            if cmd == "move":
                self._draw_pending_polygon(draw, polygon_points, fill_color)
                polygon_points = [points[0]]
                current_pos = points[0]
            elif cmd == "line":
                polygon_points.append(points[0])
                current_pos = points[0]
            elif cmd == "curve" and current_pos:
                curve_points = self.bezier_curve(current_pos, points[0], points[1], points[2], 8)
                polygon_points.extend(curve_points[1:])
                current_pos = points[2]
            elif cmd == "quad" and current_pos:
                curve_points = self.quad_bezier(current_pos, points[0], points[1], 6)
                polygon_points.extend(curve_points[1:])
                current_pos = points[1]
            elif cmd == "close":
                self._draw_pending_polygon(draw, polygon_points, fill_color)
                polygon_points = []

        self._draw_pending_polygon(draw, polygon_points, fill_color)
        return img

    @staticmethod
    def _draw_pending_polygon(
        draw: Any,
        points: list[tuple[float, float]],
        color: tuple[int, int, int, int],
    ) -> None:
        if len(points) >= 3:
            flat_points = [coord for point in points for coord in point]
            with contextlib.suppress(Exception):
                draw.polygon(flat_points, fill=color)

    @staticmethod
    def bezier_curve(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        steps: int = 10,
    ) -> list[tuple[float, float]]:
        """计算三次贝塞尔曲线点"""
        points = []
        for index in range(steps + 1):
            t = index / steps
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt
            x = mt3 * p0[0] + 3 * mt2 * t * p1[0] + 3 * mt * t2 * p2[0] + t3 * p3[0]
            y = mt3 * p0[1] + 3 * mt2 * t * p1[1] + 3 * mt * t2 * p2[1] + t3 * p3[1]
            points.append((x, y))
        return points

    @staticmethod
    def quad_bezier(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        steps: int = 8,
    ) -> list[tuple[float, float]]:
        """计算二次贝塞尔曲线点"""
        points = []
        for index in range(steps + 1):
            t = index / steps
            mt = 1 - t
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            points.append((x, y))
        return points

    def create_fallback_icon(self, size: int, color: str) -> Any:
        """创建降级图标（简单形状）"""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        fill_color = self.parse_color(color)
        padding = size // 6
        draw.ellipse([padding, padding, size - padding, size - padding], fill=fill_color)
        return img


__all__ = ["IconRenderer"]
