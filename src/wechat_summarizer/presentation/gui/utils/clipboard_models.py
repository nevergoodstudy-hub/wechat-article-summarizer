"""Models and limits for clipboard link detection."""

from __future__ import annotations

from dataclasses import dataclass

MAX_TEXT_LENGTH = 100000
MAX_URLS = 50
MAX_URL_LENGTH = 2048


@dataclass
class DetectionResult:
    """检测结果"""

    links: list[str]
    source: str
    message: str
    duplicates_removed: int = 0
    invalid_removed: int = 0


__all__ = [
    "MAX_TEXT_LENGTH",
    "MAX_URLS",
    "MAX_URL_LENGTH",
    "DetectionResult",
]
