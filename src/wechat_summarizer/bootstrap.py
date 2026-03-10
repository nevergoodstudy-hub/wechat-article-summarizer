"""应用运行时与组合根。"""

from __future__ import annotations

from dataclasses import dataclass

from .infrastructure.config import AppSettings, Container, get_settings


@dataclass(slots=True, frozen=True)
class AppRuntime:
    """绑定应用运行时依赖。"""

    settings: AppSettings
    container: Container


def build_app_runtime(
    *,
    settings: AppSettings | None = None,
    container: Container | None = None,
) -> AppRuntime:
    """构建显式应用运行时。"""
    if container is not None:
        resolved_settings = settings or container.settings
        if settings is not None and container.settings is not settings:
            raise ValueError("container.settings 与 settings 必须引用同一配置对象")
        return AppRuntime(settings=resolved_settings, container=container)

    resolved_settings = settings or get_settings()
    return AppRuntime(
        settings=resolved_settings,
        container=Container(settings=resolved_settings),
    )
