"""GUI 工具模块"""

from .clipboard_detector import (
    AutoLinkDetector,
    BrowserDetector,
    ClipboardManager,
    DetectionResult,
    WeChatLinkDetector,
)
from .display import DisplayHelper
from .theme_manager import ThemeManager
from .windows_integration import Windows11StyleHelper, WindowsIntegration

__all__ = [
    "AutoLinkDetector",
    "BrowserDetector",
    "ClipboardManager",
    "DetectionResult",
    "DisplayHelper",
    "ThemeManager",
    "WeChatLinkDetector",
    "Windows11StyleHelper",
    "WindowsIntegration",
]
