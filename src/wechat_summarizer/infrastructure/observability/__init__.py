"""可观测性模块

提供 metrics 收集、分布式追踪和结构化日志支持。
"""

from .metrics import MetricsCollector, MetricsConfig, get_metrics
from .tracing import (
    TracingConfig,
    TracingManager,
    get_tracing_manager,
    init_tracing,
    trace_span,
    trace_use_case,
    traced,
)

__all__ = [
    # Metrics
    "MetricsCollector",
    "MetricsConfig",
    # Tracing
    "TracingConfig",
    "TracingManager",
    "get_metrics",
    "get_tracing_manager",
    "init_tracing",
    "trace_span",
    "trace_use_case",
    "traced",
]
