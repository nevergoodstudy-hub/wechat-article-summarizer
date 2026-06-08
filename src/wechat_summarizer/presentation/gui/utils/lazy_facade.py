"""Convenience helpers for GUI lazy loading."""

from __future__ import annotations

from collections.abc import Callable

from .lazy_loader import LazyLoader


def lazy(module_path: str, class_name: str, preload: bool = False) -> Callable:
    """Decorator that registers a component for lazy loading."""

    def decorator(cls):
        loader = LazyLoader()
        name = f"{module_path}.{class_name}"
        loader.register(name, module_path, class_name, preload)
        return cls

    return decorator


def preload_components(*names: str) -> None:
    """Preload multiple registered lazy components."""
    loader = LazyLoader()
    for name in names:
        loader.preload_component(name)


__all__ = ["lazy", "preload_components"]
