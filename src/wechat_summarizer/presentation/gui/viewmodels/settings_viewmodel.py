"""设置视图模型"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .base import BaseViewModel, Observable

if TYPE_CHECKING:
    from ....infrastructure.config import Container


class SettingsViewModel(BaseViewModel):
    """设置视图模型

    管理应用设置的显示和编辑。
    """

    def __init__(self, container: Container):
        super().__init__()
        self._container = container
        settings = container.settings

        # 主题设置
        self._appearance_mode = Observable("light")

        # 默认选项
        self._default_summarizer = Observable(settings.default_summary_method)
        self._default_exporter = Observable("html")

        # API 配置状态（只读显示）
        self._openai_configured = Observable(bool(settings.openai.api_key.get_secret_value()))
        self._anthropic_configured = Observable(bool(settings.anthropic.api_key.get_secret_value()))
        self._zhipu_configured = Observable(bool(settings.zhipu.api_key.get_secret_value()))

        # 导出配置状态
        self._obsidian_configured = Observable(bool(settings.export.obsidian_vault_path))
        self._notion_configured = Observable(
            bool(settings.export.notion_api_key.get_secret_value())
            and bool(settings.export.notion_database_id)
        )
        self._onenote_configured = Observable(bool(settings.export.onenote_client_id))

        # 缓存信息
        self._cache_size = Observable("")
        self._cache_count = Observable(0)

        # 刷新缓存统计
        self._refresh_cache_stats()

    # region Properties

    @property
    def appearance_mode(self) -> str:
        return self._appearance_mode.value

    @appearance_mode.setter
    def appearance_mode(self, value: str) -> None:
        self._appearance_mode.value = value

    @property
    def default_summarizer(self) -> str:
        return self._default_summarizer.value

    @default_summarizer.setter
    def default_summarizer(self, value: str) -> None:
        self._default_summarizer.value = value

    @property
    def default_exporter(self) -> str:
        return self._default_exporter.value

    @default_exporter.setter
    def default_exporter(self, value: str) -> None:
        self._default_exporter.value = value

    @property
    def openai_configured(self) -> bool:
        return self._openai_configured.value

    @property
    def anthropic_configured(self) -> bool:
        return self._anthropic_configured.value

    @property
    def zhipu_configured(self) -> bool:
        return self._zhipu_configured.value

    @property
    def obsidian_configured(self) -> bool:
        return self._obsidian_configured.value

    @property
    def notion_configured(self) -> bool:
        return self._notion_configured.value

    @property
    def onenote_configured(self) -> bool:
        return self._onenote_configured.value

    @property
    def cache_size(self) -> str:
        return self._cache_size.value

    @property
    def cache_count(self) -> int:
        return self._cache_count.value

    # endregion

    # region Subscriptions

    def subscribe_appearance_mode(self, callback: Callable[[str, str], None]) -> Callable[[], None]:
        return self._appearance_mode.subscribe(callback)

    # endregion

    # region Methods

    def _refresh_cache_stats(self) -> None:
        """刷新缓存统计信息"""
        try:
            storage = self._container.storage
            if storage is not None:
                stats = storage.get_stats()
                self._cache_count.value = stats.total_entries

                # 格式化大小
                size_bytes = stats.total_size_bytes
                if size_bytes < 1024:
                    self._cache_size.value = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    self._cache_size.value = f"{size_bytes / 1024:.1f} KB"
                else:
                    self._cache_size.value = f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                self._cache_size.value = "N/A"
                self._cache_count.value = 0
        except Exception:
            self._cache_size.value = "N/A"
            self._cache_count.value = 0

    def clear_cache(self) -> int:
        """清空缓存

        Returns:
            清理的条目数量
        """
        try:
            storage = self._container.storage
            if storage is not None:
                count = storage.clear_all()
                self._refresh_cache_stats()
                return count
            return 0
        except Exception:
            return 0

    def cleanup_expired_cache(self) -> int:
        """清理过期缓存

        Returns:
            清理的条目数量
        """
        try:
            storage = self._container.storage
            if storage is not None:
                count = storage.cleanup_expired()
                self._refresh_cache_stats()
                return count
            return 0
        except Exception:
            return 0

    def get_config_summary(self) -> dict[str, bool]:
        """获取配置摘要

        Returns:
            各项配置是否已配置的字典
        """
        return {
            "OpenAI": self.openai_configured,
            "Anthropic": self.anthropic_configured,
            "智谱": self.zhipu_configured,
            "Obsidian": self.obsidian_configured,
            "Notion": self.notion_configured,
            "OneNote": self.onenote_configured,
        }

    # endregion
