"""共享工具"""

from datetime import datetime, timezone

from .logger import get_logger, logger, setup_logger
from .retry import async_retry, retry
from .text import (
    chunk_text,
    clean_whitespace,
    count_words,
    normalize_url,
    remove_html_tags,
    truncate_text,
)


def utc_now() -> datetime:
    """返回当前 UTC 时间（带时区信息），替代 datetime.now() 的无时区调用"""
    return datetime.now(timezone.utc)


__all__ = [
    "async_retry",
    "chunk_text",
    "clean_whitespace",
    "count_words",
    "get_logger",
    # Logger
    "logger",
    "normalize_url",
    "remove_html_tags",
    # Retry
    "retry",
    "setup_logger",
    # Text
    "truncate_text",
    # Datetime
    "utc_now",
]
