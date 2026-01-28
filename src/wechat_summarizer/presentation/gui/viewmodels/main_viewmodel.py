"""主视图模型"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseViewModel
from .single_process_viewmodel import SingleProcessViewModel
from .batch_process_viewmodel import BatchProcessViewModel
from .settings_viewmodel import SettingsViewModel

if TYPE_CHECKING:
    from ....infrastructure.config import Container


class MainViewModel(BaseViewModel):
    """主视图模型

    作为应用的顶层视图模型，管理子视图模型。
    """

    def __init__(self, container: Container):
        super().__init__()
        self._container = container

        # 子视图模型
        self.single_process = SingleProcessViewModel(container)
        self.batch_process = BatchProcessViewModel(container)
        self.settings = SettingsViewModel(container)

        # 应用信息
        self._app_version = "2.0.0"
        self._app_name = "微信公众号文章总结器"

    @property
    def app_version(self) -> str:
        return self._app_version

    @property
    def app_name(self) -> str:
        return self._app_name

    def get_available_summarizers(self) -> list[tuple[str, bool, str]]:
        """获取可用的摘要器列表"""
        return self.single_process.get_available_summarizers()

    def get_available_exporters(self) -> list[tuple[str, bool, str]]:
        """获取可用的导出器列表"""
        return self.single_process.get_available_exporters()
