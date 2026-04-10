"""结构化日志模块 - 基于 structlog

提供 structlog 结构化日志层，与 loguru 共存：
- structlog 负责结构化上下文（key-value）、处理器链
- loguru 继续作为底层 handler（文件、控制台输出）

使用方式:
    from wechat_summarizer.shared.utils.structured_logging import get_struct_logger
    log = get_struct_logger(__name__)
    log.info("article_fetched", url="https://...", duration_ms=1234)
"""

from __future__ import annotations

import logging
import sys
from typing import Any

_structlog_available = True
try:
    import structlog
    from structlog.types import Processor
except ImportError:
    _structlog_available = False
    structlog = None  # type: ignore
    Processor = Any  # type: ignore


def _loguru_sink_processor(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> str:
    """将 structlog 事件转发到 loguru 的处理器"""
    from loguru import logger as loguru_logger
    level = str(event_dict.pop("level", method_name)).upper()
    event = str(event_dict.pop("event", ""))

    # 构建 key=value 后缀
    extra_parts = []
    for k, v in event_dict.items():
        if k not in ("timestamp", "_record", "_logger"):
            extra_parts.append(f"{k}={v}")

    message: str = event
    if extra_parts:
        message = f"{event} | {' '.join(extra_parts)}"

    # 映射到 loguru 级别
    log_fn = getattr(loguru_logger.opt(depth=6), level.lower(), loguru_logger.info)
    log_fn(message)

    return message


def configure_structlog(
    json_format: bool = False,
    log_level: str = "INFO",
) -> None:
    """配置 structlog 全局设置

    Args:
        json_format: 是否使用 JSON 格式（生产环境）
        log_level: 最低日志级别
    """
    if not _structlog_available:
        return

    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    if json_format:
        # 生产环境: JSON 渲染
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        # 开发环境: 转发到 loguru（保持 loguru 的彩色输出）
        processors.append(_loguru_sink_processor)  # type: ignore[arg-type]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr)
        if json_format
        else structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_struct_logger(name: str | None = None, **initial_bindings: Any) -> Any:
    """获取 structlog 结构化 logger

    Args:
        name: 模块名称
        **initial_bindings: 初始绑定的上下文数据

    Returns:
        structlog BoundLogger（structlog 不可用时返回 loguru fallback）
    """
    if not _structlog_available:
        # Fallback: 返回 loguru logger
        from loguru import logger as loguru_logger

        return loguru_logger.bind(module=name or __name__, **initial_bindings)

    log = structlog.get_logger(name or __name__)
    if initial_bindings:
        log = log.bind(**initial_bindings)
    return log


def bind_contextvars(**kwargs: Any) -> dict[str, Any]:
    """绑定上下文变量到当前任务/线程

    Args:
        **kwargs: 要绑定的上下文数据（如 request_id, user_id）

    Returns:
        上下文绑定结果（structlog 不可用时返回空字典）
    """
    if not _structlog_available:
        return {}
    bound = structlog.contextvars.bind_contextvars(**kwargs)
    return bound if isinstance(bound, dict) else {}


def unbind_contextvars(*keys: str) -> None:
    """解绑上下文变量"""
    if not _structlog_available:
        return
    structlog.contextvars.unbind_contextvars(*keys)


def clear_contextvars() -> None:
    """清除所有上下文变量"""
    if not _structlog_available:
        return
    structlog.contextvars.clear_contextvars()
