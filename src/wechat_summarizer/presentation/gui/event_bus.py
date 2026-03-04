"""GUI事件总线 — 跨组件通信

实现发布/订阅模式，使 Frame/Page 组件之间可以松耦合通信，
避免直接引用其他组件或通过 app.py 中转。

典型事件:
- "summarizer_status_changed"  — API密钥保存后通知其他页面刷新
- "navigate"                   — 请求页面切换
- "theme_changed"              — 主题切换
- "status_update"              — 状态栏更新
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from loguru import logger


class GUIEventBus:
    """轻量级事件总线 (Mediator / Pub-Sub)"""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    # ---- 核心 API ----

    def subscribe(self, event: str, handler: Callable[..., Any]) -> Callable[[], None]:
        """订阅事件

        Args:
            event: 事件名称
            handler: 回调函数，签名 (**data) -> None

        Returns:
            取消订阅的函数
        """
        self._handlers[event].append(handler)

        def _unsubscribe() -> None:
            self.unsubscribe(event, handler)

        return _unsubscribe

    def publish(self, event: str, **data: Any) -> None:
        """发布事件

        Args:
            event: 事件名称
            **data: 传递给所有订阅者的关键字参数
        """
        for handler in self._handlers[event]:
            try:
                handler(**data)
            except Exception:
                logger.opt(exception=True).warning(
                    f"事件处理器异常: event={event}, handler={handler.__qualname__}"
                )

    def unsubscribe(self, event: str, handler: Callable[..., Any]) -> None:
        """取消订阅

        Args:
            event: 事件名称
            handler: 要移除的回调函数
        """
        handlers = self._handlers.get(event)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def clear(self) -> None:
        """清除所有订阅"""
        self._handlers.clear()
