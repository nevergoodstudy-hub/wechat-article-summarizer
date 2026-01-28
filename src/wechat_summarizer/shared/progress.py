"""进度跟踪器模块

提供进度跟踪、ETA计算和速率计算功能，用于批量处理和导出任务。
采用指数平滑算法(Exponential Smoothing Algorithm)计算ETA，这是业界标准做法。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from loguru import logger


@dataclass
class ProgressInfo:
    """进度信息数据类"""
    
    current: int = 0                    # 当前已完成数量
    total: int = 0                      # 总数量
    percentage: float = 0.0             # 完成百分比 (0-100)
    elapsed_seconds: float = 0.0        # 已用时间（秒）
    eta_seconds: float = 0.0            # 预计剩余时间（秒）
    rate: float = 0.0                   # 处理速率（每秒处理数量）
    current_item: str = ""              # 当前处理项名称
    
    @property
    def elapsed_formatted(self) -> str:
        """格式化已用时间"""
        return format_duration(self.elapsed_seconds)
    
    @property
    def eta_formatted(self) -> str:
        """格式化ETA"""
        if self.eta_seconds <= 0 or self.eta_seconds == float('inf'):
            return "--:--"
        return format_duration(self.eta_seconds)
    
    @property
    def rate_formatted(self) -> str:
        """格式化速率"""
        if self.rate < 0.01:
            return "计算中..."
        elif self.rate < 1:
            return f"{self.rate:.2f} 篇/秒"
        else:
            return f"{self.rate:.1f} 篇/秒"
    
    @property
    def progress_text(self) -> str:
        """进度文本 (例如: 3/10)"""
        return f"{self.current}/{self.total}"
    
    @property
    def percentage_text(self) -> str:
        """百分比文本 (例如: 30.0%)"""
        return f"{self.percentage:.1f}%"
    
    def to_log_string(self) -> str:
        """生成日志记录字符串"""
        parts = [
            f"进度: {self.progress_text} ({self.percentage_text})",
            f"已用: {self.elapsed_formatted}",
            f"ETA: {self.eta_formatted}",
            f"速率: {self.rate_formatted}",
        ]
        if self.current_item:
            parts.insert(0, f"[{self.current_item}]")
        return " | ".join(parts)


def format_duration(seconds: float) -> str:
    """将秒数格式化为可读的时间字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串 (mm:ss 或 hh:mm:ss)
    """
    if seconds < 0 or seconds == float('inf'):
        return "--:--"
    
    seconds = int(seconds)
    
    if seconds < 60:
        return f"00:{seconds:02d}"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class ProgressTracker:
    """进度跟踪器
    
    使用指数平滑算法计算ETA，提供平滑稳定的预测。
    
    用法示例:
        tracker = ProgressTracker(total=100)
        for i in range(100):
            do_work()
            tracker.update(1, current_item=f"item_{i}")
            print(tracker.get_info().to_log_string())
    """
    
    def __init__(
        self,
        total: int,
        smoothing_factor: float = 0.3,
        callback: Optional[Callable[[ProgressInfo], None]] = None,
        log_interval: int = 1,
    ):
        """初始化进度跟踪器
        
        Args:
            total: 总任务数量
            smoothing_factor: 指数平滑因子 (0-1)
                0 = 使用平均速度（更稳定但反应慢）
                1 = 使用瞬时速度（反应快但波动大）
                推荐值: 0.3
            callback: 进度更新回调函数，每次update时调用
            log_interval: 日志记录间隔（每处理多少项记录一次日志）
        """
        self._total = max(1, total)
        self._current = 0
        self._smoothing_factor = max(0.0, min(1.0, smoothing_factor))
        self._callback = callback
        self._log_interval = max(1, log_interval)
        
        # 时间追踪
        self._start_time: float = time.time()
        self._last_update_time: float = self._start_time
        
        # 平滑速率（使用指数平滑算法）
        self._smoothed_rate: float = 0.0
        
        # 当前处理项
        self._current_item: str = ""
        
        # 日志计数器
        self._log_counter: int = 0
    
    @property
    def total(self) -> int:
        """总任务数量"""
        return self._total
    
    @property
    def current(self) -> int:
        """当前已完成数量"""
        return self._current
    
    @property
    def percentage(self) -> float:
        """完成百分比 (0-100)"""
        return (self._current / self._total) * 100.0
    
    @property
    def is_complete(self) -> bool:
        """是否已完成"""
        return self._current >= self._total
    
    def reset(self, total: Optional[int] = None):
        """重置进度跟踪器
        
        Args:
            total: 新的总数量（可选，不传则保持原值）
        """
        if total is not None:
            self._total = max(1, total)
        
        self._current = 0
        self._start_time = time.time()
        self._last_update_time = self._start_time
        self._smoothed_rate = 0.0
        self._current_item = ""
        self._log_counter = 0
    
    def update(self, increment: int = 1, current_item: str = "") -> ProgressInfo:
        """更新进度
        
        Args:
            increment: 增量（默认1）
            current_item: 当前处理项的名称/描述
            
        Returns:
            当前进度信息
        """
        now = time.time()
        
        # 更新当前计数
        self._current = min(self._current + increment, self._total)
        self._current_item = current_item
        
        # 计算本次更新的时间间隔
        time_delta = now - self._last_update_time
        self._last_update_time = now
        
        # 计算瞬时速率（避免除零）
        if time_delta > 0.001:
            instant_rate = increment / time_delta
        else:
            instant_rate = self._smoothed_rate
        
        # 使用指数平滑算法更新速率
        if self._smoothed_rate == 0:
            # 第一次更新，直接使用瞬时速率
            self._smoothed_rate = instant_rate
        else:
            # 指数平滑: new_rate = alpha * instant_rate + (1 - alpha) * old_rate
            self._smoothed_rate = (
                self._smoothing_factor * instant_rate + 
                (1 - self._smoothing_factor) * self._smoothed_rate
            )
        
        # 获取进度信息
        info = self.get_info()
        
        # 调用回调
        if self._callback:
            try:
                self._callback(info)
            except Exception as e:
                logger.warning(f"进度回调执行失败: {e}")
        
        # 定期记录日志
        self._log_counter += 1
        if self._log_counter >= self._log_interval:
            self._log_counter = 0
            logger.info(f"📊 {info.to_log_string()}")
        
        return info
    
    def get_info(self) -> ProgressInfo:
        """获取当前进度信息
        
        Returns:
            ProgressInfo对象，包含所有进度相关信息
        """
        now = time.time()
        elapsed = now - self._start_time
        
        # 计算ETA
        remaining = self._total - self._current
        if self._smoothed_rate > 0 and remaining > 0:
            eta = remaining / self._smoothed_rate
        elif self._current >= self._total:
            eta = 0.0
        else:
            eta = float('inf')
        
        return ProgressInfo(
            current=self._current,
            total=self._total,
            percentage=self.percentage,
            elapsed_seconds=elapsed,
            eta_seconds=eta,
            rate=self._smoothed_rate,
            current_item=self._current_item,
        )
    
    def set_callback(self, callback: Optional[Callable[[ProgressInfo], None]]):
        """设置进度更新回调函数
        
        Args:
            callback: 回调函数，接收ProgressInfo参数
        """
        self._callback = callback
    
    def finish(self) -> ProgressInfo:
        """标记任务完成
        
        Returns:
            最终进度信息
        """
        self._current = self._total
        info = self.get_info()
        
        # 记录完成日志
        logger.success(f"✅ 任务完成！总用时: {info.elapsed_formatted}")
        
        return info


class BatchProgressTracker(ProgressTracker):
    """批量任务进度跟踪器
    
    扩展了ProgressTracker，增加了成功/失败计数等功能。
    """
    
    def __init__(
        self,
        total: int,
        smoothing_factor: float = 0.3,
        callback: Optional[Callable[[ProgressInfo], None]] = None,
        log_interval: int = 1,
    ):
        super().__init__(total, smoothing_factor, callback, log_interval)
        self._success_count = 0
        self._failure_count = 0
        self._failures: list[tuple[str, str]] = []  # (item_name, error_message)
    
    @property
    def success_count(self) -> int:
        """成功数量"""
        return self._success_count
    
    @property
    def failure_count(self) -> int:
        """失败数量"""
        return self._failure_count
    
    @property
    def failures(self) -> list[tuple[str, str]]:
        """失败项列表"""
        return self._failures.copy()
    
    def reset(self, total: Optional[int] = None):
        """重置跟踪器"""
        super().reset(total)
        self._success_count = 0
        self._failure_count = 0
        self._failures.clear()
    
    def update_success(self, current_item: str = "") -> ProgressInfo:
        """记录成功完成一项
        
        Args:
            current_item: 当前项名称
            
        Returns:
            进度信息
        """
        self._success_count += 1
        return self.update(1, current_item)
    
    def update_failure(self, current_item: str = "", error: str = "") -> ProgressInfo:
        """记录失败一项
        
        Args:
            current_item: 当前项名称
            error: 错误信息
            
        Returns:
            进度信息
        """
        self._failure_count += 1
        self._failures.append((current_item, error))
        return self.update(1, current_item)
    
    def get_summary(self) -> str:
        """获取任务摘要
        
        Returns:
            包含成功/失败统计的摘要字符串
        """
        info = self.get_info()
        return (
            f"完成: {info.progress_text} | "
            f"成功: {self._success_count} | "
            f"失败: {self._failure_count} | "
            f"用时: {info.elapsed_formatted}"
        )
