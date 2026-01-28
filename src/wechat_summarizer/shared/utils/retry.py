"""重试工具"""

from __future__ import annotations

import asyncio
import functools
import random
import time
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from loguru import logger

from ..constants import DEFAULT_MAX_RETRIES

P = ParamSpec("P")
T = TypeVar("T")


def retry(
    max_attempts: int = DEFAULT_MAX_RETRIES,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    同步重试装饰器

    Args:
        max_attempts: 最大尝试次数
        exceptions: 需要重试的异常类型
        delay: 初始延迟秒数
        backoff: 延迟倍增因子
        jitter: 是否添加随机抖动
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"重试{max_attempts}次后仍然失败: {e}")
                        raise

                    # 计算延迟
                    wait_time = current_delay
                    if jitter:
                        wait_time *= 0.5 + random.random()

                    logger.warning(f"第{attempt}次尝试失败: {e}, {wait_time:.1f}秒后重试...")

                    time.sleep(wait_time)
                    current_delay *= backoff

            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = DEFAULT_MAX_RETRIES,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    异步重试装饰器

    Args:
        max_attempts: 最大尝试次数
        exceptions: 需要重试的异常类型
        delay: 初始延迟秒数
        backoff: 延迟倍增因子
        jitter: 是否添加随机抖动
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Exception | None = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(f"重试{max_attempts}次后仍然失败: {e}")
                        raise

                    # 计算延迟
                    wait_time = current_delay
                    if jitter:
                        wait_time *= 0.5 + random.random()

                    logger.warning(f"第{attempt}次尝试失败: {e}, {wait_time:.1f}秒后重试...")

                    await asyncio.sleep(wait_time)
                    current_delay *= backoff

            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator
