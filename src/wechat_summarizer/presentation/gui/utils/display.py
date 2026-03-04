"""屏幕显示辅助工具

提供:
- 屏幕刷新率检测 (支持 60Hz ~ 480Hz)
- 高刷新率屏幕识别
- 最优动画FPS计算
"""

from __future__ import annotations

import sys

from loguru import logger


class DisplayHelper:
    """屏幕显示辅助工具 - 检测刷新率等屏幕参数

    支持高刷新率屏幕 (120Hz, 144Hz, 165Hz, 240Hz 等)
    """

    _detected_refresh_rate: int | None = None
    _detection_attempted: bool = False

    # 常见刷新率映射，用于验证检测结果的合理性
    COMMON_REFRESH_RATES = [60, 75, 90, 100, 120, 144, 165, 180, 200, 240, 360, 480]

    @classmethod
    def get_refresh_rate(cls) -> int:
        """获取屏幕刷新率 (Hz)

        Returns:
            int: 刷新率，默认 60Hz
        """
        if cls._detected_refresh_rate is not None:
            return cls._detected_refresh_rate

        if cls._detection_attempted:
            return 60  # 已尝试过检测但失败，返回默认值

        cls._detection_attempted = True
        cls._detected_refresh_rate = cls._detect_refresh_rate()
        return cls._detected_refresh_rate

    @classmethod
    def _detect_refresh_rate(cls) -> int:
        """检测屏幕刷新率

        尝试多种方法检测：
        1. Windows API (ctypes)
        2. win32api (如果可用)
        3. 默认 60Hz
        """
        refresh_rate = 60  # 默认值

        # 方法 1: 使用 ctypes 调用 Windows API (仅 Windows)
        if sys.platform != "win32":
            return refresh_rate
        try:
            import ctypes
            from ctypes import wintypes

            # DEVMODEW 结构体定义
            class DEVMODEW(ctypes.Structure):
                _fields_ = [
                    ("dmDeviceName", wintypes.WCHAR * 32),
                    ("dmSpecVersion", wintypes.WORD),
                    ("dmDriverVersion", wintypes.WORD),
                    ("dmSize", wintypes.WORD),
                    ("dmDriverExtra", wintypes.WORD),
                    ("dmFields", wintypes.DWORD),
                    ("dmPositionX", wintypes.LONG),
                    ("dmPositionY", wintypes.LONG),
                    ("dmDisplayOrientation", wintypes.DWORD),
                    ("dmDisplayFixedOutput", wintypes.DWORD),
                    ("dmColor", wintypes.SHORT),
                    ("dmDuplex", wintypes.SHORT),
                    ("dmYResolution", wintypes.SHORT),
                    ("dmTTOption", wintypes.SHORT),
                    ("dmCollate", wintypes.SHORT),
                    ("dmFormName", wintypes.WCHAR * 32),
                    ("dmLogPixels", wintypes.WORD),
                    ("dmBitsPerPel", wintypes.DWORD),
                    ("dmPelsWidth", wintypes.DWORD),
                    ("dmPelsHeight", wintypes.DWORD),
                    ("dmDisplayFlags", wintypes.DWORD),
                    ("dmDisplayFrequency", wintypes.DWORD),
                    # ... 其他字段省略
                ]

            user32 = ctypes.windll.user32
            dm = DEVMODEW()
            dm.dmSize = ctypes.sizeof(DEVMODEW)

            # ENUM_CURRENT_SETTINGS = -1
            if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(dm)):
                detected = dm.dmDisplayFrequency
                # 验证检测结果的合理性
                if detected > 0 and detected <= 500:
                    refresh_rate = detected
                    logger.debug(f"📺 检测到屏幕刷新率: {refresh_rate}Hz (Windows API)")
        except Exception as e:
            logger.debug(f"使用 Windows API 检测刷新率失败: {e}")

        # 方法 2: 尝试使用 win32api (如果 ctypes 失败)
        if refresh_rate == 60:
            try:
                import win32api

                device = win32api.EnumDisplayDevices(None, 0)
                settings = win32api.EnumDisplaySettings(device.DeviceName, -1)
                detected = settings.DisplayFrequency
                if detected > 0 and detected <= 500:
                    refresh_rate = detected
                    logger.debug(f"📺 检测到屏幕刷新率: {refresh_rate}Hz (win32api)")
            except ImportError:
                pass
            except Exception as e:
                logger.debug(f"使用 win32api 检测刷新率失败: {e}")

        return refresh_rate

    @classmethod
    def is_high_refresh_rate(cls) -> bool:
        """检查是否为高刷新率屏幕 (>60Hz)"""
        return cls.get_refresh_rate() > 60

    @classmethod
    def get_optimal_fps(cls) -> int:
        """获取最优动画FPS

        对于高刷新率屏幕，使用屏幕刷新率的一半或全刷新率：
        - 60Hz -> 60fps
        - 120Hz -> 120fps
        - 144Hz -> 144fps
        - 240Hz -> 120fps (对于超高刷新率，限制到 120fps 以节省资源)
        """
        refresh_rate = cls.get_refresh_rate()

        # 对于超高刷新率屏幕，限制最大FPS以避免过度消耗资源
        if refresh_rate > 165:
            return 120

        return refresh_rate

    @classmethod
    def get_frame_time(cls) -> float:
        """获取单帧时长（毫秒）"""
        fps = max(cls.get_optimal_fps(), 1)
        return 1000.0 / fps

    @classmethod
    def reset_detection(cls):
        """重置检测状态，强制重新检测"""
        cls._detected_refresh_rate = None
        cls._detection_attempted = False
