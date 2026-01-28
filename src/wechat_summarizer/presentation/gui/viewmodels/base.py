"""基础 ViewModel 类

提供 MVVM 架构中视图模型的基础功能：
- 属性变更通知
- 命令绑定
- 状态管理
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class ViewModelState(Enum):
    """视图模型状态"""

    IDLE = auto()  # 空闲
    LOADING = auto()  # 加载中
    SUCCESS = auto()  # 成功
    ERROR = auto()  # 错误


@dataclass
class PropertyChangedEvent:
    """属性变更事件"""

    property_name: str
    old_value: Any
    new_value: Any


class Observable(Generic[T]):
    """可观察属性

    用于实现数据绑定，当值变化时自动通知订阅者。
    """

    def __init__(self, initial_value: T):
        self._value = initial_value
        self._callbacks: list[Callable[[T, T], None]] = []

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T) -> None:
        if self._value != new_value:
            old_value = self._value
            self._value = new_value
            self._notify(old_value, new_value)

    def subscribe(self, callback: Callable[[T, T], None]) -> Callable[[], None]:
        """订阅值变化

        Args:
            callback: 回调函数，接收旧值和新值

        Returns:
            取消订阅的函数
        """
        self._callbacks.append(callback)
        return lambda: self._callbacks.remove(callback)

    def _notify(self, old_value: T, new_value: T) -> None:
        for callback in self._callbacks:
            try:
                callback(old_value, new_value)
            except Exception:
                pass  # 忽略回调异常


@dataclass
class Command:
    """命令对象

    用于封装用户操作，支持执行和可执行性检查。
    """

    execute: Callable[[], None]
    can_execute: Callable[[], bool] = field(default=lambda: True)
    description: str = ""

    def __call__(self) -> None:
        if self.can_execute():
            self.execute()


class BaseViewModel:
    """基础视图模型

    所有 ViewModel 的基类，提供：
    - 状态管理
    - 属性变更通知
    - 错误处理
    """

    def __init__(self):
        self._state = Observable(ViewModelState.IDLE)
        self._error_message = Observable("")
        self._is_busy = Observable(False)
        self._property_changed_callbacks: list[Callable[[PropertyChangedEvent], None]] = []

    @property
    def state(self) -> ViewModelState:
        return self._state.value

    @state.setter
    def state(self, value: ViewModelState) -> None:
        self._state.value = value

    @property
    def error_message(self) -> str:
        return self._error_message.value

    @error_message.setter
    def error_message(self, value: str) -> None:
        self._error_message.value = value

    @property
    def is_busy(self) -> bool:
        return self._is_busy.value

    @is_busy.setter
    def is_busy(self, value: bool) -> None:
        self._is_busy.value = value

    def subscribe_state(self, callback: Callable[[ViewModelState, ViewModelState], None]) -> Callable[[], None]:
        """订阅状态变化"""
        return self._state.subscribe(callback)

    def subscribe_error(self, callback: Callable[[str, str], None]) -> Callable[[], None]:
        """订阅错误消息变化"""
        return self._error_message.subscribe(callback)

    def subscribe_busy(self, callback: Callable[[bool, bool], None]) -> Callable[[], None]:
        """订阅忙碌状态变化"""
        return self._is_busy.subscribe(callback)

    def on_property_changed(self, callback: Callable[[PropertyChangedEvent], None]) -> Callable[[], None]:
        """订阅属性变更事件"""
        self._property_changed_callbacks.append(callback)
        return lambda: self._property_changed_callbacks.remove(callback)

    def _notify_property_changed(self, property_name: str, old_value: Any, new_value: Any) -> None:
        """通知属性变更"""
        event = PropertyChangedEvent(property_name, old_value, new_value)
        for callback in self._property_changed_callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def set_error(self, message: str) -> None:
        """设置错误状态"""
        self.error_message = message
        self.state = ViewModelState.ERROR
        self.is_busy = False

    def set_success(self) -> None:
        """设置成功状态"""
        self.error_message = ""
        self.state = ViewModelState.SUCCESS
        self.is_busy = False

    def set_loading(self) -> None:
        """设置加载状态"""
        self.error_message = ""
        self.state = ViewModelState.LOADING
        self.is_busy = True

    def reset(self) -> None:
        """重置状态"""
        self.error_message = ""
        self.state = ViewModelState.IDLE
        self.is_busy = False
