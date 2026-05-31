"""GUI主窗口协调器（薄入口）

阶段性重构：将启动流程与具体 GUI 实现解耦，
为后续从 `app.py` 逐步拆分到 frames/viewmodels 提供稳定入口。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class MainWindow:
    """GUI 启动协调器（薄层）。"""

    def __init__(
        self,
        app_factory: Callable[..., Any],
        *,
        container: Any,
        settings: Any,
    ) -> None:
        self._app_factory = app_factory
        self._container = container
        self._settings = settings
        self._app: Any | None = None

    def build(self) -> Any:
        """创建底层 GUI 应用实例。"""
        self._app = self._app_factory(container=self._container, settings=self._settings)
        return self._app

    def run(self) -> None:
        """构建并运行 GUI。"""
        app = self.build()
        app.run()
