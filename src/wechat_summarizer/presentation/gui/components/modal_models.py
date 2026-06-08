"""Data models for modal components."""

from __future__ import annotations

from enum import Enum


class ModalSize(Enum):
    """模态框尺寸"""

    SMALL = (400, 200)
    MEDIUM = (500, 300)
    LARGE = (700, 500)
    FULLSCREEN = (0, 0)


__all__ = ["ModalSize"]
