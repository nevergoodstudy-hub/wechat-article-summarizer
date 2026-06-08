"""Data models for GUI performance monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PerformanceLevel(Enum):
    """性能等级"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class PerformanceMetrics:
    """性能指标"""

    fps: float = 0.0
    frame_time_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """转为字典(不含敏感信息)"""
        return {
            "fps": round(self.fps, 1),
            "frame_time_ms": round(self.frame_time_ms, 2),
            "memory_mb": round(self.memory_mb, 1),
            "cpu_percent": round(self.cpu_percent, 1),
            "timestamp": self.timestamp,
        }


@dataclass
class SlowOperation:
    """慢操作记录"""

    name: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name[:50],
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
        }


@dataclass
class OperationSample:
    """Measured operation sample."""

    name: str
    duration_ms: float
    memory_mb: float
    cpu_percent: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name[:50],
            "duration_ms": round(self.duration_ms, 2),
            "memory_mb": round(self.memory_mb, 1),
            "cpu_percent": round(self.cpu_percent, 1),
            "timestamp": self.timestamp,
        }


__all__ = [
    "OperationSample",
    "PerformanceLevel",
    "PerformanceMetrics",
    "SlowOperation",
]
