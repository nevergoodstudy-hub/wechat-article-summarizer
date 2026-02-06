"""GUI 工具模块"""

from .windows_integration import WindowsIntegration, Windows11StyleHelper
from .display import DisplayHelper
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
    "Windows11StyleHelper",
    "DisplayHelper",
    "ThemeManager",
    "AutoLinkDetector",
    "WeChatLinkDetector",
    "ClipboardManager",
    "BrowserDetector",
    "DetectionResult",
]
