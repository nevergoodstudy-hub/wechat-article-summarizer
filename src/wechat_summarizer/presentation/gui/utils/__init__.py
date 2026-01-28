"""GUI 工具模块"""

from .windows_integration import WindowsIntegration
from .theme_manager import ThemeManager
from .clipboard_detector import (
    AutoLinkDetector,
    WeChatLinkDetector,
    ClipboardManager,
    BrowserDetector,
    DetectionResult,
)

__all__ = [
    "WindowsIntegration",
    "ThemeManager",
    "AutoLinkDetector",
    "WeChatLinkDetector",
    "ClipboardManager",
    "BrowserDetector",
    "DetectionResult",
]
