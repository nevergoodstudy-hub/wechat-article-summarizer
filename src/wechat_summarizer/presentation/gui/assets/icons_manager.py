"""Icon manager with bounded caching."""

from __future__ import annotations

from typing import Any

from .icons_models import IconSize, IconStyle
from .icons_paths import ICON_PATHS
from .icons_renderer import IconRenderer
from .icons_runtime import PIL_AVAILABLE, ImageTk


class IconManager:
    """图标管理器"""

    MAX_PATH_LENGTH = 10000

    def __init__(self) -> None:
        """初始化图标管理器"""
        self._cache: dict[tuple[str, int, str], Any] = {}
        self._cache_limit = 200
        self._renderer = IconRenderer()

    def get_icon(
        self,
        name: str,
        size: IconSize = IconSize.MEDIUM,
        color: str = "#FFFFFF",
        style: IconStyle = IconStyle.OUTLINED,
    ) -> Any | None:
        """获取图标"""
        if not PIL_AVAILABLE:
            return None

        if not self._validate_color(color):
            color = "#FFFFFF"

        cache_key = (name, size.value, color)
        if cache_key in self._cache:
            return self._cache[cache_key]
        if name not in ICON_PATHS:
            return None

        icon = self._create_icon(name, size.value, color)
        if len(self._cache) >= self._cache_limit:
            self._cache.pop(next(iter(self._cache)))
        self._cache[cache_key] = icon
        return icon

    @staticmethod
    def _validate_color(color: str) -> bool:
        """验证颜色格式"""
        return IconRenderer.validate_color(color)

    @staticmethod
    def _parse_color(color: str) -> tuple[int, int, int, int]:
        """解析颜色为RGBA"""
        return IconRenderer.parse_color(color)

    def _create_icon(self, name: str, size: int, color: str) -> Any | None:
        """创建图标 - 使用SVG路径渲染"""
        if not PIL_AVAILABLE:
            return None

        path_data = ICON_PATHS.get(name, "")
        if len(path_data) > self.MAX_PATH_LENGTH:
            return self._create_fallback_icon(size, color)
        return self._renderer.render(path_data, size, color)

    def _render_with_cairosvg(self, path_data: str, size: int, color: str) -> Any | None:
        """使用cairosvg渲染SVG"""
        return self._renderer._render_with_cairosvg(path_data, size, color)

    def _render_with_pil(self, path_data: str, size: int, color: str) -> Any | None:
        """使用PIL手动渲染SVG路径"""
        return self._renderer.render_with_pil(path_data, size, color)

    @staticmethod
    def _draw_polygon(draw: Any, points: list[tuple], color: tuple) -> None:
        """绘制填充多边形"""
        return IconRenderer._draw_pending_polygon(draw, points, color)

    @staticmethod
    def _bezier_curve(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        p3: tuple[float, float],
        steps: int = 10,
    ) -> list[tuple[float, float]]:
        """计算三次贝塞尔曲线点"""
        return IconRenderer.bezier_curve(p0, p1, p2, p3, steps)

    @staticmethod
    def _quad_bezier(
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        steps: int = 8,
    ) -> list[tuple[float, float]]:
        """计算二次贝塞尔曲线点"""
        return IconRenderer.quad_bezier(p0, p1, p2, steps)

    def _create_fallback_icon(self, size: int, color: str) -> Any:
        """创建降级图标（简单形状）"""
        return self._renderer.create_fallback_icon(size, color)

    def get_icon_tk(
        self, name: str, size: IconSize = IconSize.MEDIUM, color: str = "#FFFFFF"
    ) -> Any | None:
        """获取Tkinter兼容的图标"""
        if not PIL_AVAILABLE:
            return None

        icon = self.get_icon(name, size, color)
        if icon is None:
            return None
        return ImageTk.PhotoImage(icon)

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()

    @staticmethod
    def list_icons() -> list[str]:
        """列出所有可用图标"""
        return list(ICON_PATHS.keys())


__all__ = ["IconManager"]
