"""异步任务执行器

提供一个全局共享的后台事件循环，用于在 GUI 应用中执行异步任务。
避免每次创建新的事件循环造成的性能开销，并允许 HTTP 连接池复用。

最佳实践参考：
- asyncio.run_coroutine_threadsafe: 线程安全地提交协程到事件循环
- 单例模式：全局共享一个后台事件循环线程
- concurrent.futures.Future: 实现跨线程同步等待
"""

from __future__ import annotations

import asyncio
import atexit
import threading
from concurrent.futures import Future
from typing import Any, Callable, Coroutine, TypeVar

from loguru import logger

T = TypeVar("T")


class AsyncTaskExecutor:
    """
    异步任务执行器（单例）
    
    在独立的后台线程中运行一个持久的事件循环，
    提供线程安全的接口从主线程（如 GUI 线程）提交异步任务。
    
    优势：
    - 避免重复创建/销毁事件循环的开销
    - HTTP 连接池等资源可在同一事件循环中复用
    - 提供同步和异步两种任务提交方式
    
    使用方法：
        executor = get_async_executor()
        
        # 方式1: 同步等待结果
        result = executor.run_sync(async_function())
        
        # 方式2: 带回调的异步执行
        executor.run_with_callback(
            async_function(),
            on_success=lambda result: print(f"成功: {result}"),
            on_error=lambda error: print(f"失败: {error}"),
            ui_callback=root.after,  # Tkinter 的线程安全回调
        )
        
        # 方式3: 提交任务并获取 Future
        future = executor.submit(async_function())
        result = future.result(timeout=10)
    """
    
    _instance: AsyncTaskExecutor | None = None
    _lock = threading.Lock()
    
    def __new__(cls) -> AsyncTaskExecutor:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()
        self._stopped = False
        self._initialized = True
        
        # 自动启动
        self._start_loop()
        
        # 注册退出清理
        atexit.register(self.shutdown)
        
        logger.debug("AsyncTaskExecutor 初始化完成")
    
    def _start_loop(self) -> None:
        """启动后台事件循环线程"""
        if self._thread is not None and self._thread.is_alive():
            return
        
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._started.set()
            logger.debug("后台事件循环已启动")
            
            try:
                self._loop.run_forever()
            finally:
                # 清理待处理的任务
                pending = asyncio.all_tasks(self._loop)
                for task in pending:
                    task.cancel()
                
                # 等待取消完成
                if pending:
                    self._loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
                
                self._loop.close()
                logger.debug("后台事件循环已关闭")
        
        self._thread = threading.Thread(target=run_loop, daemon=True, name="AsyncExecutorLoop")
        self._thread.start()
        
        # 等待事件循环启动
        self._started.wait(timeout=5.0)
    
    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """获取事件循环"""
        if self._loop is None or not self._loop.is_running():
            self._start_loop()
        return self._loop  # type: ignore
    
    @property
    def is_running(self) -> bool:
        """检查事件循环是否运行中"""
        return self._loop is not None and self._loop.is_running()
    
    def submit(self, coro: Coroutine[Any, Any, T]) -> Future[T]:
        """
        提交协程任务并返回 Future
        
        Args:
            coro: 要执行的协程
            
        Returns:
            concurrent.futures.Future 对象，可用于获取结果或等待完成
        """
        if self._stopped:
            raise RuntimeError("执行器已停止")
        
        return asyncio.run_coroutine_threadsafe(coro, self.loop)
    
    def run_sync(self, coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
        """
        同步执行协程并等待结果
        
        Args:
            coro: 要执行的协程
            timeout: 超时时间（秒），None 表示无限等待
            
        Returns:
            协程的返回值
            
        Raises:
            TimeoutError: 超时
            Exception: 协程执行过程中的异常
        """
        future = self.submit(coro)
        return future.result(timeout=timeout)
    
    def run_with_callback(
        self,
        coro: Coroutine[Any, Any, T],
        on_success: Callable[[T], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        ui_callback: Callable[[int, Callable], None] | None = None,
    ) -> Future[T]:
        """
        执行协程并在完成时调用回调
        
        Args:
            coro: 要执行的协程
            on_success: 成功回调，接收协程返回值
            on_error: 错误回调，接收异常
            ui_callback: UI 线程回调函数（如 tkinter 的 root.after）
                         签名：ui_callback(delay_ms, callback_func)
                         
        Returns:
            Future 对象
        """
        future = self.submit(coro)
        
        def done_callback(fut: Future):
            try:
                result = fut.result()
                if on_success:
                    if ui_callback:
                        ui_callback(0, lambda: on_success(result))
                    else:
                        on_success(result)
            except Exception as e:
                if on_error:
                    if ui_callback:
                        ui_callback(0, lambda err=e: on_error(err))
                    else:
                        on_error(e)
        
        future.add_done_callback(done_callback)
        return future
    
    def shutdown(self, wait: bool = True, timeout: float = 5.0) -> None:
        """
        关闭执行器
        
        Args:
            wait: 是否等待当前任务完成
            timeout: 等待超时时间
        """
        if self._stopped:
            return
        
        self._stopped = True
        
        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        if wait and self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        
        logger.debug("AsyncTaskExecutor 已关闭")
    
    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        if cls._instance is not None:
            cls._instance.shutdown(wait=False)
            cls._instance = None


# 便捷函数
def get_async_executor() -> AsyncTaskExecutor:
    """获取全局异步执行器实例"""
    return AsyncTaskExecutor()


def run_async(coro: Coroutine[Any, Any, T], timeout: float | None = None) -> T:
    """便捷函数：同步执行协程"""
    return get_async_executor().run_sync(coro, timeout=timeout)


def submit_async(coro: Coroutine[Any, Any, T]) -> Future[T]:
    """便捷函数：提交异步任务"""
    return get_async_executor().submit(coro)


class GUIAsyncHelper:
    """
    GUI 异步辅助类
    
    封装了常见的 GUI + 异步操作模式，简化代码。
    
    使用方法：
        helper = GUIAsyncHelper(root.after)
        
        # 执行异步操作并更新 UI
        helper.run(
            self._do_search(query),
            on_success=self._display_results,
            on_error=self._show_error,
        )
    """
    
    def __init__(self, ui_callback: Callable[[int, Callable], None]) -> None:
        """
        初始化
        
        Args:
            ui_callback: UI 线程回调函数，通常是 tkinter 的 root.after
        """
        self._ui_callback = ui_callback
        self._executor = get_async_executor()
    
    def run(
        self,
        coro: Coroutine[Any, Any, T],
        on_success: Callable[[T], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> Future[T]:
        """
        执行异步任务
        
        Args:
            coro: 要执行的协程
            on_success: 成功回调（在 UI 线程中执行）
            on_error: 错误回调（在 UI 线程中执行）
            
        Returns:
            Future 对象
        """
        return self._executor.run_with_callback(
            coro,
            on_success=on_success,
            on_error=on_error,
            ui_callback=self._ui_callback,
        )
    
    def run_in_ui(self, callback: Callable[[], None], delay_ms: int = 0) -> None:
        """
        在 UI 线程中执行回调
        
        Args:
            callback: 要执行的回调函数
            delay_ms: 延迟毫秒数
        """
        self._ui_callback(delay_ms, callback)
