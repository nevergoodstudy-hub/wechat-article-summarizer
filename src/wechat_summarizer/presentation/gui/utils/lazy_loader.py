"""Threaded lazy component loader."""

from __future__ import annotations

import importlib
import logging
import threading
import time
import tkinter as tk
import weakref
from collections.abc import Callable

from .lazy_models import (
    ALLOWED_MODULE_PREFIX,
    MAX_CACHED_COMPONENTS,
    MAX_CONCURRENT_LOADS,
    MAX_RETRY_COUNT,
    LazyComponent,
    LoadResult,
    LoadState,
)

logger = logging.getLogger(__name__)


class LazyLoader:
    """Singleton manager for lazy GUI component loading."""

    _instance: LazyLoader | None = None
    _initialized: bool

    def __new__(cls) -> LazyLoader:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        instance = cls._instance
        assert instance is not None
        return instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._components: dict[str, LazyComponent] = {}
        self._loaded_cache: dict[str, type] = {}
        self._loading_tasks: set[str] = set()
        self._load_lock = threading.Lock()
        self._callbacks: dict[str, list[Callable[[LoadResult], None]]] = {}
        self._instances: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

    def register(
        self,
        name: str,
        module_path: str,
        class_name: str,
        preload: bool = False,
        fallback: type[tk.Widget] | None = None,
    ) -> None:
        """Register a lazy-loadable component."""
        if not self._validate_module_path(module_path):
            logger.error("模块路径不允许: %s", module_path)
            return

        self._components[name] = LazyComponent(
            module_path=module_path,
            class_name=class_name,
            preload=preload,
            fallback=fallback,
        )

        if preload:
            self.preload_component(name)

    def _validate_module_path(self, module_path: str) -> bool:
        """Validate module path before dynamic imports."""
        if not module_path.startswith(ALLOWED_MODULE_PREFIX):
            return False

        return not (".." in module_path or module_path.startswith("/"))

    def preload_component(self, name: str) -> None:
        """Start loading a component in a daemon thread."""
        if name not in self._components:
            return

        thread = threading.Thread(target=lambda: self._load_component_sync(name), daemon=True)
        thread.start()

    def load_component(
        self,
        name: str,
        callback: Callable[[LoadResult], None] | None = None,
    ) -> None:
        """Load a component asynchronously and call back with the result."""
        if name in self._loaded_cache:
            if callback:
                callback(LoadResult(state=LoadState.SUCCESS, component=self._loaded_cache[name]))
            return

        with self._load_lock:
            if len(self._loading_tasks) >= MAX_CONCURRENT_LOADS:
                if callback:
                    callback(LoadResult(state=LoadState.ERROR, error="加载队列已满，请稍后重试"))
                return

            self._callbacks.setdefault(name, [])
            if callback:
                self._callbacks[name].append(callback)

            if name in self._loading_tasks:
                return

            self._loading_tasks.add(name)

        thread = threading.Thread(target=lambda: self._complete_async_load(name), daemon=True)
        thread.start()

    def _complete_async_load(self, name: str) -> None:
        result = self._load_component_sync(name)

        with self._load_lock:
            self._loading_tasks.discard(name)
            callbacks = self._callbacks.pop(name, [])

        for callback in callbacks:
            try:
                callback(result)
            except Exception as exc:
                logger.error("回调执行失败: %s", exc)

    def _load_component_sync(self, name: str) -> LoadResult:
        """Load a registered component synchronously."""
        start_time = time.time()

        if name not in self._components:
            return LoadResult(state=LoadState.ERROR, error=f"组件未注册: {name}")

        component = self._components[name]
        retry_count = 0

        while retry_count < MAX_RETRY_COUNT:
            try:
                module = importlib.import_module(component.module_path)
                cls = getattr(module, component.class_name)

                self._loaded_cache[name] = cls
                component._loaded_class = cls
                component._load_state = LoadState.SUCCESS
                self._cleanup_cache()

                load_time = (time.time() - start_time) * 1000
                logger.info("组件加载成功: %s (%.1fms)", name, load_time)
                return LoadResult(state=LoadState.SUCCESS, component=cls, load_time_ms=load_time)

            except Exception as exc:
                retry_count += 1
                logger.warning(
                    "组件加载失败 (尝试 %s/%s): %s",
                    retry_count,
                    MAX_RETRY_COUNT,
                    exc,
                )
                time.sleep(0.5)

        error_msg = f"组件加载失败: {name}"
        component._load_state = LoadState.ERROR
        component._error = error_msg
        return LoadResult(state=LoadState.ERROR, error=error_msg)

    def _cleanup_cache(self) -> None:
        """Trim the loaded component cache when it exceeds the configured size."""
        if len(self._loaded_cache) > MAX_CACHED_COMPONENTS:
            keys = list(self._loaded_cache.keys())
            for key in keys[: len(keys) // 2]:
                self._loaded_cache.pop(key, None)

    def get_component(self, name: str) -> type | None:
        """Return a component class, loading synchronously if needed."""
        if name in self._loaded_cache:
            return self._loaded_cache[name]

        result = self._load_component_sync(name)
        return result.component

    def is_loaded(self, name: str) -> bool:
        """Return whether a component class is already cached."""
        return name in self._loaded_cache

    def unregister(self, name: str) -> None:
        """Remove a component registration and cached class."""
        self._components.pop(name, None)
        self._loaded_cache.pop(name, None)

    def clear_cache(self) -> None:
        """Clear loaded component cache."""
        self._loaded_cache.clear()


__all__ = ["LazyLoader"]
