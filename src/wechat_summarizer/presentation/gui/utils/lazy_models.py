"""Data models and safety limits for GUI lazy loading."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from typing import Any

MAX_CONCURRENT_LOADS = 5
LOAD_TIMEOUT_SECONDS = 30
MAX_RETRY_COUNT = 3
MAX_CACHED_COMPONENTS = 50
ALLOWED_MODULE_PREFIX = "wechat_summarizer."


class LoadState(Enum):
    """Lazy component loading state."""

    IDLE = "idle"
    LOADING = "loading"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class LoadResult:
    """Result returned after a lazy component load attempt."""

    state: LoadState
    component: Any | None = None
    error: str | None = None
    load_time_ms: float = 0


class LazyComponent:
    """Lazy-loadable component registration."""

    def __init__(
        self,
        module_path: str,
        class_name: str,
        preload: bool = False,
        fallback: type[tk.Widget] | None = None,
    ) -> None:
        self.module_path = module_path
        self.class_name = class_name
        self.preload = preload
        self.fallback = fallback
        self._loaded_class: type | None = None
        self._load_state = LoadState.IDLE
        self._error: str | None = None


__all__ = [
    "ALLOWED_MODULE_PREFIX",
    "LOAD_TIMEOUT_SECONDS",
    "MAX_CACHED_COMPONENTS",
    "MAX_CONCURRENT_LOADS",
    "MAX_RETRY_COUNT",
    "LazyComponent",
    "LoadResult",
    "LoadState",
]
