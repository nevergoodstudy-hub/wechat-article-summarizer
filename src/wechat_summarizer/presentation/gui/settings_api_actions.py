"""API-key action handlers for the settings page."""

from __future__ import annotations

from typing import Any

from loguru import logger

from .dialogs import confirm_clear_api_keys
from .styles.colors import ModernColors
from .utils.i18n import tr


class SettingsApiActionsMixin:
    """Handle API key visibility, save, and clear actions."""

    def _toggle_key_visibility(self: Any, provider: str) -> None:
        entry = self._api_key_entries.get(provider)
        if not entry:
            return
        show_var = getattr(self, f"_{provider}_show_var", None)
        entry.configure(show="" if show_var and show_var.get() else "•")

    def _save_api_keys(self: Any) -> None:
        saved_count = 0
        api_keys = {}
        for provider, entry in self._api_key_entries.items():
            key = entry.get().strip()
            self.gui.user_prefs.set_api_key(provider, key)
            if key:
                saved_count += 1
                api_keys[provider] = key
        self.gui.container.settings_workflow_service.reload_summarizers(api_keys)
        self.gui._summarizer_info = self.gui._get_summarizer_info()
        self.update_summarizer_status_display()
        self.gui._refresh_summarizer_menus()
        if saved_count > 0:
            self.api_status_label.configure(
                text=tr("✓ 已保存 {count} 个 API 密钥").format(count=saved_count),
                text_color=ModernColors.SUCCESS,
            )
            logger.success(f"已保存 {saved_count} 个 API 密钥")
        else:
            self.api_status_label.configure(
                text=tr("✓ 密钥已清除"), text_color=ModernColors.WARNING
            )
            logger.info("API 密钥已清除")
        self.gui._set_status(tr("API密钥已更新"), ModernColors.SUCCESS)

    def _clear_api_keys(self: Any) -> None:
        if not confirm_clear_api_keys():
            return
        for provider, entry in self._api_key_entries.items():
            entry.delete(0, "end")
            self.gui.user_prefs.set_api_key(provider, "")
        self.gui._summarizer_info = self.gui._get_summarizer_info()
        self.update_summarizer_status_display()
        self.gui._refresh_summarizer_menus()
        self.api_status_label.configure(
            text=tr("✓ 所有密钥已清除"), text_color=ModernColors.WARNING
        )
        logger.info("所有 API 密钥已清除")
