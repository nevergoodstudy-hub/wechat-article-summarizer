"""频率限制器

控制对微信API的请求频率，防止因请求过于频繁而被封禁。
使用令牌桶算法实现平滑的速率限制。
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from loguru import logger


@dataclass
class RateLimitConfig:
    """频率限制配置"""

    requests_per_minute: int = 20  # 每分钟最大请求数
    min_interval: float = 2.0  # 最小请求间隔（秒）
    max_interval: float = 5.0  # 最大请求间隔（秒）
    burst_size: int = 5  # 突发请求数
    adaptive: bool = True  # 是否启用自适应调整
    
    @property
    def base_interval(self) -> float:
        """基准间隔时间"""
        return 60.0 / self.requests_per_minute


class RateLimiter:
    """
    频率限制器
    
    使用滑动窗口算法控制请求频率，支持自适应调整。
    当检测到速率限制错误时会自动增加等待时间。
    
    使用方法:
        limiter = RateLimiter(config)
        
        async with limiter:
            # 执行请求
            response = await client.get(url)
            
        # 或者手动等待
        await limiter.wait()
        response = await client.get(url)
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        self._config = config or RateLimitConfig()
        self._request_times: deque[float] = deque(maxlen=self._config.requests_per_minute)
        self._lock = asyncio.Lock()
        self._last_request_time: float = 0.0
        self._current_interval: float = self._config.base_interval
        self._consecutive_errors: int = 0
        self._total_requests: int = 0
        self._total_waits: float = 0.0

    @property
    def config(self) -> RateLimitConfig:
        """获取配置"""
        return self._config

    @property
    def current_interval(self) -> float:
        """当前请求间隔"""
        return self._current_interval

    @property
    def stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_requests": self._total_requests,
            "total_wait_time": round(self._total_waits, 2),
            "avg_wait_time": (
                round(self._total_waits / self._total_requests, 2)
                if self._total_requests > 0
                else 0
            ),
            "current_interval": round(self._current_interval, 2),
            "consecutive_errors": self._consecutive_errors,
        }

    async def wait(self) -> float:
        """等待直到可以发送下一个请求
        
        Returns:
            实际等待的时间（秒）
        """
        async with self._lock:
            now = time.time()
            wait_time = self._calculate_wait_time(now)

            if wait_time > 0:
                logger.debug(f"频率限制：等待 {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
                self._total_waits += wait_time

            self._record_request()
            return wait_time

    def _calculate_wait_time(self, now: float) -> float:
        """计算需要等待的时间"""
        # 检查最小间隔
        if self._last_request_time > 0:
            elapsed = now - self._last_request_time
            if elapsed < self._current_interval:
                return self._current_interval - elapsed

        # 检查滑动窗口
        if len(self._request_times) >= self._config.requests_per_minute:
            oldest = self._request_times[0]
            window_elapsed = now - oldest
            if window_elapsed < 60.0:
                # 等到窗口滑过
                return 60.0 - window_elapsed + 0.1

        return 0.0

    def _record_request(self) -> None:
        """记录请求时间"""
        now = time.time()
        self._request_times.append(now)
        self._last_request_time = now
        self._total_requests += 1

    def report_success(self) -> None:
        """报告请求成功
        
        用于自适应调整：成功时逐渐减少间隔
        """
        if not self._config.adaptive:
            return

        self._consecutive_errors = 0
        
        # 成功时缓慢减少间隔
        if self._current_interval > self._config.min_interval:
            self._current_interval = max(
                self._config.min_interval,
                self._current_interval * 0.95,
            )
            logger.debug(f"请求成功，调整间隔为 {self._current_interval:.2f}s")

    def report_error(self, is_rate_limit: bool = False) -> None:
        """报告请求失败
        
        Args:
            is_rate_limit: 是否为频率限制错误
        """
        if not self._config.adaptive:
            return

        self._consecutive_errors += 1

        if is_rate_limit:
            # 频率限制错误：大幅增加间隔
            self._current_interval = min(
                self._config.max_interval,
                self._current_interval * 2.0,
            )
            logger.warning(
                f"检测到频率限制，增加间隔为 {self._current_interval:.2f}s"
            )
        else:
            # 其他错误：小幅增加间隔
            self._current_interval = min(
                self._config.max_interval,
                self._current_interval * 1.2,
            )

    def reset(self) -> None:
        """重置限制器状态"""
        self._request_times.clear()
        self._last_request_time = 0.0
        self._current_interval = self._config.base_interval
        self._consecutive_errors = 0
        logger.debug("频率限制器已重置")

    async def __aenter__(self) -> "RateLimiter":
        """异步上下文管理器入口"""
        await self.wait()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        if exc_type is None:
            self.report_success()
        else:
            # 根据异常类型判断是否为频率限制
            is_rate_limit = "rate" in str(exc_val).lower() if exc_val else False
            self.report_error(is_rate_limit=is_rate_limit)


class AdaptiveRateLimiter(RateLimiter):
    """
    自适应频率限制器
    
    基于响应时间动态调整请求间隔。
    """

    def __init__(self, config: RateLimitConfig | None = None) -> None:
        super().__init__(config)
        self._response_times: deque[float] = deque(maxlen=10)

    def record_response_time(self, response_time: float) -> None:
        """记录响应时间
        
        Args:
            response_time: 响应耗时（秒）
        """
        self._response_times.append(response_time)
        
        if len(self._response_times) >= 5:
            avg_time = sum(self._response_times) / len(self._response_times)
            
            # 如果平均响应时间过长，增加请求间隔
            if avg_time > 5.0:
                self._current_interval = min(
                    self._config.max_interval,
                    self._current_interval * 1.1,
                )
                logger.debug(
                    f"响应时间较长 ({avg_time:.2f}s)，"
                    f"调整间隔为 {self._current_interval:.2f}s"
                )
            elif avg_time < 2.0 and self._consecutive_errors == 0:
                self._current_interval = max(
                    self._config.min_interval,
                    self._current_interval * 0.9,
                )
