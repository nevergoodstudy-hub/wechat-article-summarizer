"""日志配置 - 基于Loguru

支持：
- 结构化 JSON 日志
- request_id 追踪
- 敏感信息脱敏
- 日志文件轮转
- Windows 标准路径
"""

import sys
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Any

from loguru import logger

from ..constants import LOG_FILE_NAME

# 请求 ID 上下文变量
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """
    脱敏处理敏感信息
    
    Args:
        value: 需要脱敏的字符串
        visible_chars: 前后可见字符数
    
    Returns:
        脱敏后的字符串，如 "sk-a***xyz"
    
    Examples:
        >>> mask_sensitive("sk-abcdefghijklmnop")
        'sk-a***mnop'
        >>> mask_sensitive("short")
        '***'
    """
    if not value:
        return "***"
    if len(value) <= visible_chars * 2:
        return "***"
    return f"{value[:visible_chars]}***{value[-visible_chars:]}"


def mask_api_key(api_key: str) -> str:
    """
    专门用于API密钥的脱敏处理
    
    Args:
        api_key: API密钥字符串
    
    Returns:
        脱敏后的字符串
    """
    if not api_key:
        return "[未配置]"
    return mask_sensitive(api_key, visible_chars=4)


def setup_logger(
    level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Path | None = None,
    json_format: bool = False,
    rotation: str = "10 MB",
    retention: str = "30 days",
    compression: str = "zip",
) -> None:
    """
    配置日志

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
        log_to_file: 是否写入文件
        log_dir: 日志目录，默认使用 Windows 标准路径 (AppData/Local)
        json_format: 是否使用JSON格式（便于日志收集系统）
        rotation: 日志文件轮转策略 (例如 "10 MB", "1 day")
        retention: 日志保留时间 (例如 "30 days", "5 files")
        compression: 压缩格式 ("zip", "gz", "bz2")
    """
    # 移除默认处理器
    logger.remove()

    if json_format:
        # 结构化 JSON 日志（便于日志收集系统如 ELK）
        logger.add(
            sys.stderr,
            level=level,
            format="{message}",
            serialize=True,
        )
    else:
        # 人类可读格式（控制台）
        # 在 Windows 终端中使用更好的颜色支持
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            colorize=True,
        )

    # 文件输出
    if log_to_file:
        if log_dir is None:
            # 使用 Windows 标准路径 (AppData/Local/WechatSummarizer/logs)
            try:
                from ...infrastructure.config.paths import get_log_dir
                log_dir = get_log_dir()
            except ImportError:
                # 回退到用户目录
                log_dir = Path.home() / ".wechat_summarizer" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / LOG_FILE_NAME
        logger.add(
            log_file,
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            enqueue=True,  # 异步写入，提高性能
        )


def get_logger(name: str = __name__):
    """获取带名称的logger"""
    return logger.bind(name=name)


# -------------------- Request ID 追踪 --------------------

def generate_request_id() -> str:
    """生成新的请求 ID"""
    return str(uuid.uuid4())[:8]


def set_request_id(request_id: str | None = None) -> str:
    """设置当前请求的 request_id"""
    if request_id is None:
        request_id = generate_request_id()
    _request_id_var.set(request_id)
    return request_id


def get_request_id() -> str | None:
    """获取当前请求的 request_id"""
    return _request_id_var.get()


def clear_request_id() -> None:
    """清除当前请求的 request_id"""
    _request_id_var.set(None)


# -------------------- 结构化日志记录 --------------------

def log_event(
    event: str,
    level: str = "INFO",
    **kwargs: Any,
) -> None:
    """
    记录结构化事件

    Args:
        event: 事件名称
        level: 日志级别
        **kwargs: 额外的事件属性

    Examples:
        log_event("article_fetched", url="https://...", duration_ms=1234)
        log_event("summary_generated", model="ollama", tokens=500)
    """
    # 添加 request_id
    request_id = get_request_id()
    if request_id:
        kwargs["request_id"] = request_id

    # 构建消息
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(
        f"[{event}] " + " ".join(f"{k}={v}" for k, v in kwargs.items()),
        **{"event": event, **kwargs},
    )


def log_article_fetch(
    url: str,
    scraper: str,
    duration_ms: int,
    success: bool = True,
    error: str | None = None,
) -> None:
    """记录文章抓取事件"""
    level = "INFO" if success else "WARNING"
    log_event(
        "article_fetched",
        level=level,
        url=url[:100],  # 截断过长 URL
        scraper=scraper,
        duration_ms=duration_ms,
        success=success,
        error=error,
    )


def log_summary_generated(
    model: str,
    duration_ms: int,
    tokens: int = 0,
    success: bool = True,
    error: str | None = None,
) -> None:
    """记录摘要生成事件"""
    level = "INFO" if success else "WARNING"
    log_event(
        "summary_generated",
        level=level,
        model=model,
        duration_ms=duration_ms,
        tokens=tokens,
        success=success,
        error=error,
    )


def log_export(
    target: str,
    path: str | None = None,
    success: bool = True,
    error: str | None = None,
) -> None:
    """记录导出事件"""
    level = "INFO" if success else "WARNING"
    log_event(
        "article_exported",
        level=level,
        target=target,
        path=path,
        success=success,
        error=error,
    )


# 导出主logger
__all__ = [
    "logger",
    "setup_logger",
    "get_logger",
    "mask_sensitive",
    "mask_api_key",
    "generate_request_id",
    "set_request_id",
    "get_request_id",
    "clear_request_id",
    "log_event",
    "log_article_fetch",
    "log_summary_generated",
    "log_export",
]
