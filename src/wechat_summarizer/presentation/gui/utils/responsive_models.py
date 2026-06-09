"""Models for responsive GUI layout."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Breakpoint(Enum):
    """断点枚举"""

    XS = "xs"
    SM = "sm"
    MD = "md"
    LG = "lg"
    XL = "xl"


@dataclass
class BreakpointConfig:
    """断点配置"""

    xs_max: int = 768
    sm_max: int = 1024
    md_max: int = 1440
    lg_max: int = 1920


__all__ = ["Breakpoint", "BreakpointConfig"]
