"""Breakpoint-aware values."""

from __future__ import annotations

from typing import Generic, TypeVar

from .responsive_breakpoints import BreakpointManager
from .responsive_models import Breakpoint

T = TypeVar("T")


class ResponsiveValue(Generic[T]):
    """响应式值 - 根据断点返回不同值"""

    def __init__(
        self,
        breakpoint_manager: BreakpointManager,
        values: dict[Breakpoint, T],
        default: T | None = None,
    ):
        self.bp_manager = breakpoint_manager
        self.values = values
        self.default = default

    def get(self) -> T | None:
        """获取当前断点对应的值"""
        breakpoint = self.bp_manager.get_current_breakpoint()
        return self.values.get(breakpoint, self.default)

    def __call__(self) -> T | None:
        return self.get()


__all__ = ["ResponsiveValue"]
