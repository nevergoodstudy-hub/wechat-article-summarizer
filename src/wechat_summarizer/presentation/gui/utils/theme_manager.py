"""主题管理器

管理 GUI 主题和外观设置。
"""

from __future__ import annotations

from collections.abc import Callable

from loguru import logger

from .theme_models import AccessibilitySettings, AppearanceMode, ContrastMode
from .theme_palettes import (
    BASE_FONT_SIZES,
    HIGH_CONTRAST_THEMES,
    THEMES,
    WECHAT_BLUE,
    WECHAT_GREEN,
)
from .theme_platform import (
    apply_appearance_mode,
    detect_system_theme,
    should_reduce_motion_for_system,
)
from .theme_storage import (
    default_accessibility_config_file,
    load_accessibility_settings,
    save_accessibility_settings,
)


class ThemeManager:
    """主题管理器"""

    _instance: ThemeManager | None = None
    _initialized: bool

    WECHAT_GREEN = WECHAT_GREEN
    WECHAT_BLUE = WECHAT_BLUE
    THEMES = THEMES
    HIGH_CONTRAST_THEMES = HIGH_CONTRAST_THEMES
    BASE_FONT_SIZES = BASE_FONT_SIZES

    def __new__(cls) -> ThemeManager:
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._current_mode: AppearanceMode = AppearanceMode.LIGHT
        self._callbacks: list[Callable[[AppearanceMode], None]] = []
        self._accessibility_callbacks: list[Callable[[AccessibilitySettings], None]] = []
        self._config_file = default_accessibility_config_file()
        self._accessibility = load_accessibility_settings(self._config_file)

    @property
    def current_mode(self) -> AppearanceMode:
        """当前外观模式"""
        return self._current_mode

    def set_mode(self, mode: AppearanceMode | str) -> None:
        """设置外观模式"""
        if isinstance(mode, str):
            mode = AppearanceMode(mode)

        if mode == self._current_mode:
            return

        self._current_mode = mode
        self._apply_mode(mode)
        self._notify_callbacks(mode)

    def _apply_mode(self, mode: AppearanceMode) -> None:
        """应用外观模式"""
        apply_appearance_mode(mode)

    def _detect_system_theme(self) -> AppearanceMode:
        """检测系统主题"""
        return detect_system_theme()

    def on_mode_changed(self, callback: Callable[[AppearanceMode], None]) -> Callable[[], None]:
        """注册主题变更回调"""
        self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

    def _notify_callbacks(self, mode: AppearanceMode) -> None:
        """通知所有回调"""
        for callback in self._callbacks:
            try:
                callback(mode)
            except Exception as e:
                logger.debug(f"Theme callback error: {e}")

    def toggle_mode(self) -> AppearanceMode:
        """切换明暗模式"""
        if self._current_mode == AppearanceMode.DARK:
            self.set_mode(AppearanceMode.LIGHT)
        else:
            self.set_mode(AppearanceMode.DARK)
        return self._current_mode

    @property
    def accessibility(self) -> AccessibilitySettings:
        """获取可访问性设置"""
        return self._accessibility

    def set_font_scale(self, scale: float) -> None:
        """设置字体缩放"""
        scale = max(
            AccessibilitySettings.MIN_FONT_SCALE, min(AccessibilitySettings.MAX_FONT_SCALE, scale)
        )

        if scale == self._accessibility.font_scale:
            return

        self._accessibility.font_scale = scale
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()

    def increase_font_scale(self, step: float = 0.1) -> float:
        """增大字体"""
        new_scale = min(AccessibilitySettings.MAX_FONT_SCALE, self._accessibility.font_scale + step)
        self.set_font_scale(new_scale)
        return self._accessibility.font_scale

    def decrease_font_scale(self, step: float = 0.1) -> float:
        """减小字体"""
        new_scale = max(AccessibilitySettings.MIN_FONT_SCALE, self._accessibility.font_scale - step)
        self.set_font_scale(new_scale)
        return self._accessibility.font_scale

    def reset_font_scale(self) -> None:
        """重置字体大小"""
        self.set_font_scale(1.0)

    def get_scaled_font_size(self, size_key: str = "base") -> int:
        """获取缩放后的字体大小"""
        base_size = self.BASE_FONT_SIZES.get(size_key, 14)
        return int(base_size * self._accessibility.font_scale)

    def set_contrast_mode(self, mode: ContrastMode | str) -> None:
        """设置对比度模式"""
        if isinstance(mode, ContrastMode):
            mode = mode.value

        if mode == self._accessibility.contrast_mode:
            return

        self._accessibility.contrast_mode = mode
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()

    def toggle_high_contrast(self) -> bool:
        """切换高对比度模式"""
        if self._accessibility.contrast_mode == "normal":
            self.set_contrast_mode("high")
            return True

        self.set_contrast_mode("normal")
        return False

    def is_high_contrast(self) -> bool:
        """是否为高对比度模式"""
        return self._accessibility.contrast_mode != "normal"

    def set_reduce_motion(self, enabled: bool) -> None:
        """设置减少动画"""
        if enabled == self._accessibility.reduce_motion:
            return

        self._accessibility.reduce_motion = enabled
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()

    def toggle_reduce_motion(self) -> bool:
        """切换减少动画"""
        self.set_reduce_motion(not self._accessibility.reduce_motion)
        return self._accessibility.reduce_motion

    def should_reduce_motion(self) -> bool:
        """是否应减少动画"""
        if self._accessibility.reduce_motion:
            return True
        return should_reduce_motion_for_system()

    def set_reduce_transparency(self, enabled: bool) -> None:
        """设置减少透明度"""
        if enabled == self._accessibility.reduce_transparency:
            return

        self._accessibility.reduce_transparency = enabled
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()

    def get_colors(self, mode: AppearanceMode | None = None) -> dict[str, str]:
        """获取指定模式的颜色配置"""
        if mode is None:
            mode = self._current_mode

        if mode == AppearanceMode.SYSTEM:
            mode = self._detect_system_theme()

        mode_str = "dark" if mode == AppearanceMode.DARK else "light"

        if self.is_high_contrast():
            return self.HIGH_CONTRAST_THEMES.get(mode_str, self.HIGH_CONTRAST_THEMES["light"])

        return self.THEMES.get(mode_str, self.THEMES["light"])

    def on_accessibility_changed(
        self, callback: Callable[[AccessibilitySettings], None]
    ) -> Callable[[], None]:
        """注册可访问性设置变更回调"""
        self._accessibility_callbacks.append(callback)
        return lambda: self._accessibility_callbacks.remove(callback)

    def _notify_accessibility_callbacks(self) -> None:
        """通知可访问性回调"""
        for callback in self._accessibility_callbacks:
            try:
                callback(self._accessibility)
            except Exception as e:
                logger.debug(f"Accessibility callback error: {e}")

    def _load_accessibility_settings(self) -> None:
        """加载可访问性设置"""
        self._accessibility = load_accessibility_settings(self._config_file)

    def _save_accessibility_settings(self) -> None:
        """保存可访问性设置"""
        save_accessibility_settings(self._config_file, self._accessibility)


theme_manager = ThemeManager()


__all__ = [
    "AccessibilitySettings",
    "AppearanceMode",
    "ContrastMode",
    "ThemeManager",
    "theme_manager",
]
