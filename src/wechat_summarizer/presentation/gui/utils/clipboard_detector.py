"""Compatibility entrypoint for clipboard WeChat link detection."""

from __future__ import annotations

from .clipboard_auto import AutoLinkDetector
from .clipboard_browser import BrowserDetector
from .clipboard_manager import ClipboardManager
from .clipboard_models import MAX_TEXT_LENGTH, MAX_URL_LENGTH, MAX_URLS, DetectionResult
from .clipboard_wechat import WeChatLinkDetector

__all__ = [
    "MAX_TEXT_LENGTH",
    "MAX_URLS",
    "MAX_URL_LENGTH",
    "AutoLinkDetector",
    "BrowserDetector",
    "ClipboardManager",
    "DetectionResult",
    "WeChatLinkDetector",
]
