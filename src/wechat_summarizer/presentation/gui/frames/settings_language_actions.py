"""Language setting action helpers."""

from __future__ import annotations

from typing import Any

from loguru import logger

from ..styles.colors import ModernColors
from ..utils.i18n import set_language, tr
from ..widgets.toast_notification import ToastNotification


def apply_language_change(
    *,
    gui: Any,
    status_label: Any,
    display_value: str,
    lang_code_map: dict[str, str],
) -> None:
    """Persist and announce a GUI language change."""
    lang_code = lang_code_map.get(display_value, "auto")
    gui.user_prefs.language = lang_code
    set_language(lang_code)
    status_label.configure(
        text=tr("✓ 语言已设置为: {language}").format(language=display_value),
        text_color=ModernColors.SUCCESS,
    )
    logger.info(f"界面语言已切换: {lang_code}")
    if hasattr(gui, "_toast_manager") and gui._toast_manager:
        gui._toast_manager.info(
            tr("语言已设置为 {language}，重启应用后完全生效").format(language=display_value)
        )
        return

    ToastNotification(
        gui.root,
        tr("🌐 语言已切换"),
        tr("语言已设置为 {language}\n重启应用后完全生效").format(language=display_value),
        toast_type="info",
        duration_ms=3000,
    )


__all__ = ["apply_language_change"]
