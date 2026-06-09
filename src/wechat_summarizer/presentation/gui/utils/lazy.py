"""Compatibility entrypoint for GUI lazy loading."""

from __future__ import annotations

from .lazy_facade import lazy, preload_components
from .lazy_image import LazyImage
from .lazy_loader import LazyLoader
from .lazy_models import (
    ALLOWED_MODULE_PREFIX,
    LOAD_TIMEOUT_SECONDS,
    MAX_CACHED_COMPONENTS,
    MAX_CONCURRENT_LOADS,
    MAX_RETRY_COUNT,
    LazyComponent,
    LoadResult,
    LoadState,
)
from .lazy_widget import LazyWidget

__all__ = [
    "ALLOWED_MODULE_PREFIX",
    "LOAD_TIMEOUT_SECONDS",
    "MAX_CACHED_COMPONENTS",
    "MAX_CONCURRENT_LOADS",
    "MAX_RETRY_COUNT",
    "LazyComponent",
    "LazyImage",
    "LazyLoader",
    "LazyWidget",
    "LoadResult",
    "LoadState",
    "lazy",
    "preload_components",
]


if __name__ == "__main__":
    from .lazy_demo import run_demo

    run_demo()
