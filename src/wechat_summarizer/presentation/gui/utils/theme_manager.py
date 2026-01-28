"""主题管理器

管理 GUI 主题和外观设置。

2026年增强版:
- 可调节字体大小(100-200%)
- 高对比度模式
- 减少动画选项
- prefers-reduced-motion支持

安全措施:
- 设置范围限制
- 状态持久化验证
"""

from __future__ import annotations

import os
import json
from enum import Enum
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, asdict

from loguru import logger


class AppearanceMode(Enum):
    """外观模式"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ContrastMode(Enum):
    """对比度模式"""
    NORMAL = "normal"
    HIGH = "high"
    HIGHER = "higher"


@dataclass
class AccessibilitySettings:
    """可访问性设置"""
    font_scale: float = 1.0  # 字体缩放 (1.0 = 100%)
    contrast_mode: str = "normal"  # normal, high, higher
    reduce_motion: bool = False  # 减少动画
    reduce_transparency: bool = False  # 减少透明度
    
    # 安全限制
    MIN_FONT_SCALE = 0.8
    MAX_FONT_SCALE = 2.0
    
    def __post_init__(self):
        # 验证字体缩放范围
        self.font_scale = max(
            self.MIN_FONT_SCALE,
            min(self.MAX_FONT_SCALE, self.font_scale)
        )


class ThemeManager:
    """主题管理器

    管理应用的主题和外观设置。
    
    2026年增强:
    - 可访问性设置管理
    - 字体缩放
    - 高对比度模式
    - 减少动画选项
    """

    _instance: ThemeManager | None = None

    # 微信品牌色
    WECHAT_GREEN = "#07C160"
    WECHAT_BLUE = "#576B95"

    # 预定义主题
    THEMES = {
        "light": {
            "primary": WECHAT_GREEN,
            "secondary": WECHAT_BLUE,
            "background": "#FFFFFF",
            "surface": "#F5F5F5",
            "text": "#333333",
            "text_secondary": "#666666",
            "border": "#E0E0E0",
            "success": "#52C41A",
            "warning": "#FAAD14",
            "error": "#FF4D4F",
        },
        "dark": {
            "primary": WECHAT_GREEN,
            "secondary": WECHAT_BLUE,
            "background": "#1A1A1A",
            "surface": "#2D2D2D",
            "text": "#FFFFFF",
            "text_secondary": "#AAAAAA",
            "border": "#404040",
            "success": "#52C41A",
            "warning": "#FAAD14",
            "error": "#FF4D4F",
        },
    }
    
    # 高对比度主题
    HIGH_CONTRAST_THEMES = {
        "light": {
            "primary": "#0066CC",
            "secondary": "#003366",
            "background": "#FFFFFF",
            "surface": "#F0F0F0",
            "text": "#000000",
            "text_secondary": "#333333",
            "border": "#000000",
            "success": "#006600",
            "warning": "#CC6600",
            "error": "#CC0000",
        },
        "dark": {
            "primary": "#66B2FF",
            "secondary": "#99CCFF",
            "background": "#000000",
            "surface": "#1A1A1A",
            "text": "#FFFFFF",
            "text_secondary": "#CCCCCC",
            "border": "#FFFFFF",
            "success": "#66FF66",
            "warning": "#FFCC00",
            "error": "#FF6666",
        },
    }
    
    # 基础字体大小 (px)
    BASE_FONT_SIZES = {
        "xs": 10,
        "sm": 12,
        "base": 14,
        "lg": 16,
        "xl": 20,
        "2xl": 24,
        "3xl": 32,
        "4xl": 40,
    }

    def __new__(cls) -> ThemeManager:
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_mode = AppearanceMode.LIGHT
        self._callbacks: list[Callable[[AppearanceMode], None]] = []
        self._accessibility_callbacks: list[Callable[[AccessibilitySettings], None]] = []
        self._accessibility = AccessibilitySettings()
        
        # 配置文件路径
        self._config_file = os.path.join(
            os.path.expanduser("~"),
            ".wechat_summarizer",
            "accessibility.json"
        )
        
        # 加载保存的设置
        self._load_accessibility_settings()

    @property
    def current_mode(self) -> AppearanceMode:
        """当前外观模式"""
        return self._current_mode

    def set_mode(self, mode: AppearanceMode | str) -> None:
        """设置外观模式

        Args:
            mode: 外观模式（AppearanceMode 或字符串）
        """
        if isinstance(mode, str):
            mode = AppearanceMode(mode)

        if mode == self._current_mode:
            return

        self._current_mode = mode
        self._apply_mode(mode)
        self._notify_callbacks(mode)

    def _apply_mode(self, mode: AppearanceMode) -> None:
        """应用外观模式"""
        try:
            import customtkinter as ctk

            if mode == AppearanceMode.SYSTEM:
                ctk.set_appearance_mode("system")
            elif mode == AppearanceMode.DARK:
                ctk.set_appearance_mode("dark")
            else:
                ctk.set_appearance_mode("light")

        except ImportError:
            logger.debug("customtkinter not available for theme switching")

    def get_colors(self, mode: AppearanceMode | None = None) -> dict[str, str]:
        """获取指定模式的颜色配置

        Args:
            mode: 外观模式，None 表示当前模式

        Returns:
            颜色配置字典
        """
        if mode is None:
            mode = self._current_mode

        if mode == AppearanceMode.SYSTEM:
            # 检测系统主题
            mode = self._detect_system_theme()

        mode_str = "dark" if mode == AppearanceMode.DARK else "light"
        return self.THEMES.get(mode_str, self.THEMES["light"])

    def _detect_system_theme(self) -> AppearanceMode:
        """检测系统主题"""
        try:
            import sys

            if sys.platform == "win32":
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)

                return AppearanceMode.LIGHT if value else AppearanceMode.DARK
        except Exception:
            pass

        return AppearanceMode.LIGHT

    def on_mode_changed(self, callback: Callable[[AppearanceMode], None]) -> Callable[[], None]:
        """注册主题变更回调

        Args:
            callback: 回调函数，接收新的外观模式

        Returns:
            取消注册的函数
        """
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
        """切换明暗模式

        Returns:
            切换后的模式
        """
        if self._current_mode == AppearanceMode.DARK:
            self.set_mode(AppearanceMode.LIGHT)
        else:
            self.set_mode(AppearanceMode.DARK)
        return self._current_mode
    
    # ========== 可访问性设置 ==========
    
    @property
    def accessibility(self) -> AccessibilitySettings:
        """获取可访问性设置"""
        return self._accessibility
    
    def set_font_scale(self, scale: float) -> None:
        """设置字体缩放
        
        Args:
            scale: 缩放比例 (0.8 - 2.0)
        """
        scale = max(
            AccessibilitySettings.MIN_FONT_SCALE,
            min(AccessibilitySettings.MAX_FONT_SCALE, scale)
        )
        
        if scale == self._accessibility.font_scale:
            return
        
        self._accessibility.font_scale = scale
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()
    
    def increase_font_scale(self, step: float = 0.1) -> float:
        """增大字体
        
        Args:
            step: 增量
            
        Returns:
            新的缩放比例
        """
        new_scale = min(
            AccessibilitySettings.MAX_FONT_SCALE,
            self._accessibility.font_scale + step
        )
        self.set_font_scale(new_scale)
        return self._accessibility.font_scale
    
    def decrease_font_scale(self, step: float = 0.1) -> float:
        """减小字体
        
        Args:
            step: 减量
            
        Returns:
            新的缩放比例
        """
        new_scale = max(
            AccessibilitySettings.MIN_FONT_SCALE,
            self._accessibility.font_scale - step
        )
        self.set_font_scale(new_scale)
        return self._accessibility.font_scale
    
    def reset_font_scale(self) -> None:
        """重置字体大小"""
        self.set_font_scale(1.0)
    
    def get_scaled_font_size(self, size_key: str = "base") -> int:
        """获取缩放后的字体大小
        
        Args:
            size_key: 字体大小键 (xs, sm, base, lg, xl, 2xl, 3xl, 4xl)
            
        Returns:
            缩放后的字体大小 (px)
        """
        base_size = self.BASE_FONT_SIZES.get(size_key, 14)
        return int(base_size * self._accessibility.font_scale)
    
    def set_contrast_mode(self, mode: ContrastMode | str) -> None:
        """设置对比度模式
        
        Args:
            mode: 对比度模式
        """
        if isinstance(mode, ContrastMode):
            mode = mode.value
        
        if mode == self._accessibility.contrast_mode:
            return
        
        self._accessibility.contrast_mode = mode
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()
    
    def toggle_high_contrast(self) -> bool:
        """切换高对比度模式
        
        Returns:
            是否启用高对比度
        """
        if self._accessibility.contrast_mode == "normal":
            self.set_contrast_mode("high")
            return True
        else:
            self.set_contrast_mode("normal")
            return False
    
    def is_high_contrast(self) -> bool:
        """是否为高对比度模式"""
        return self._accessibility.contrast_mode != "normal"
    
    def set_reduce_motion(self, enabled: bool) -> None:
        """设置减少动画
        
        Args:
            enabled: 是否减少动画
        """
        if enabled == self._accessibility.reduce_motion:
            return
        
        self._accessibility.reduce_motion = enabled
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()
    
    def toggle_reduce_motion(self) -> bool:
        """切换减少动画
        
        Returns:
            是否启用减少动画
        """
        self.set_reduce_motion(not self._accessibility.reduce_motion)
        return self._accessibility.reduce_motion
    
    def should_reduce_motion(self) -> bool:
        """是否应减少动画
        
        同时检查用户设置和系统设置(prefers-reduced-motion)
        """
        if self._accessibility.reduce_motion:
            return True
        
        # 检查系统设置 (Windows)
        try:
            import sys
            if sys.platform == "win32":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Control Panel\Desktop"
                )
                # ClientAreaAnimation: 0 = off, 1 = on
                value, _ = winreg.QueryValueEx(key, "UserPreferencesMask")
                winreg.CloseKey(key)
                # 第2字节的bit 1 表示动画开关
                if isinstance(value, bytes) and len(value) > 1:
                    return not (value[1] & 0x02)
        except Exception:
            pass
        
        return False
    
    def set_reduce_transparency(self, enabled: bool) -> None:
        """设置减少透明度
        
        Args:
            enabled: 是否减少透明度
        """
        if enabled == self._accessibility.reduce_transparency:
            return
        
        self._accessibility.reduce_transparency = enabled
        self._save_accessibility_settings()
        self._notify_accessibility_callbacks()
    
    def get_colors(self, mode: AppearanceMode | None = None) -> dict[str, str]:
        """获取指定模式的颜色配置

        Args:
            mode: 外观模式，None 表示当前模式

        Returns:
            颜色配置字典
        """
        if mode is None:
            mode = self._current_mode

        if mode == AppearanceMode.SYSTEM:
            mode = self._detect_system_theme()

        mode_str = "dark" if mode == AppearanceMode.DARK else "light"
        
        # 高对比度模式使用特殊主题
        if self.is_high_contrast():
            return self.HIGH_CONTRAST_THEMES.get(mode_str, self.HIGH_CONTRAST_THEMES["light"])
        
        return self.THEMES.get(mode_str, self.THEMES["light"])
    
    def on_accessibility_changed(
        self, 
        callback: Callable[[AccessibilitySettings], None]
    ) -> Callable[[], None]:
        """注册可访问性设置变更回调
        
        Args:
            callback: 回调函数
            
        Returns:
            取消注册的函数
        """
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
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                self._accessibility = AccessibilitySettings(
                    font_scale=data.get("font_scale", 1.0),
                    contrast_mode=data.get("contrast_mode", "normal"),
                    reduce_motion=data.get("reduce_motion", False),
                    reduce_transparency=data.get("reduce_transparency", False)
                )
        except Exception as e:
            logger.warning(f"加载可访问性设置失败: {e}")
    
    def _save_accessibility_settings(self) -> None:
        """保存可访问性设置"""
        try:
            os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
            
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self._accessibility), f, indent=2)
        except Exception as e:
            logger.warning(f"保存可访问性设置失败: {e}")


# 全局实例
theme_manager = ThemeManager()
