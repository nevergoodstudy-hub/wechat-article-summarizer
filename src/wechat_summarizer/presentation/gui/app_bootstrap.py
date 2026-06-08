"""Startup and dependency bootstrap helpers for the GUI shell."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from .components.button import ButtonSize, ButtonVariant, ModernButton
from .components.card import CardStyle, ModernCard, ShadowDepth
from .ctk_compat import ctk
from .runtime_optimizations import (
    apply_low_memory_optimizations,
    check_memory_on_startup,
    is_low_memory_mode,
    show_low_memory_warning,
)
from .utils.windows_integration import Windows11StyleHelper
from .viewmodels import MainViewModel
from .widgets.helpers import GUILogHandler


class GUIBootstrapMixin:
    """Setup helpers for startup tasks, common factories, logging, and system wiring."""

    def _apply_window_style(self: Any) -> None:
        Windows11StyleHelper.apply_window_style(self.root, self._appearance_mode)

    def _init_container_and_viewmodel(self: Any) -> None:
        saved_api_keys = self.user_prefs.get_all_api_keys()
        if any(saved_api_keys.values()):
            self.container.reload_summarizers(saved_api_keys)

        self.main_viewmodel = MainViewModel(self.container)

    def _detect_summarizers(self: Any) -> None:
        self._summarizer_info = self._get_summarizer_info()

    def _detect_exporters(self: Any) -> None:
        self._exporter_info = self._get_exporter_info()

    def _show_main_window(self: Any) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self._play_welcome_animation()

    def _check_memory_on_startup(self: Any) -> None:
        check_memory_on_startup(self)

    def _show_low_memory_warning(self: Any, available_gb: float) -> None:
        show_low_memory_warning(self, available_gb)

    def _apply_low_memory_optimizations(self: Any) -> None:
        apply_low_memory_optimizations(self)

    def _is_low_memory_mode(self: Any) -> bool:
        return is_low_memory_mode(self)

    def _get_font(self: Any, size: int = 14, weight: str = "normal") -> Any:
        return ctk.CTkFont(family=self._chinese_font, size=size, weight=weight)

    def _create_modern_button(
        self: Any,
        master: Any,
        text: str,
        command: Any = None,
        variant: str = "primary",
        size: str = "medium",
        **kwargs: Any,
    ) -> ModernButton:
        variant_map = {
            "primary": ButtonVariant.PRIMARY,
            "secondary": ButtonVariant.SECONDARY,
            "ghost": ButtonVariant.GHOST,
            "danger": ButtonVariant.DANGER,
            "text": ButtonVariant.TEXT,
        }
        size_map = {
            "small": ButtonSize.SMALL,
            "medium": ButtonSize.MEDIUM,
            "large": ButtonSize.LARGE,
        }

        return ModernButton(
            master,
            text=text,
            command=command,
            variant=variant_map.get(variant, ButtonVariant.PRIMARY),
            size=size_map.get(size, ButtonSize.MEDIUM),
            theme=self._appearance_mode,
            **kwargs,
        )

    def _create_modern_card(
        self: Any,
        master: Any,
        width: int = 300,
        height: int = 200,
        style: str = "elevated",
        **kwargs: Any,
    ) -> ModernCard:
        from .components.card import CornerRadius

        style_map = {
            "solid": CardStyle.SOLID,
            "outlined": CardStyle.OUTLINED,
            "elevated": CardStyle.ELEVATED,
            "glass": CardStyle.GLASS,
        }

        return ModernCard(
            master,
            width=width,
            height=height,
            corner_radius=CornerRadius.MEDIUM,
            shadow_depth=ShadowDepth.MEDIUM,
            style=style_map.get(style, CardStyle.ELEVATED),
            theme=self._appearance_mode,
            **kwargs,
        )

    def _setup_log_handler(self: Any) -> None:
        if hasattr(self, "log_text") and self.log_text:
            self._log_handler = GUILogHandler(
                self.log_text,
                self.root,
                low_memory_mode=self.user_prefs.low_memory_mode,
            )
            self._log_handler_id = logger.add(
                self._log_handler.write,
                format="{time:HH:mm:ss} | {level:<8} | {message}",
                level="DEBUG",
                colorize=False,
            )
            logger.info("🚀 应用已启动")
            if self.user_prefs.low_memory_mode:
                self._apply_low_memory_optimizations()
                logger.info("📦 低内存模式已启用")

    def _init_system_settings(self: Any) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

        if self.user_prefs.minimize_to_tray:
            logger.debug("已启用最小化到系统托盘")

        self._sync_autostart_status()

    def _sync_autostart_status(self: Any) -> None:
        startup_folder = (
            Path.home()
            / "AppData"
            / "Roaming"
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs"
            / "Startup"
        )
        shortcut_path = startup_folder / "微信文章总结器.lnk"
        actual_enabled = shortcut_path.exists()

        if self.user_prefs.auto_start_enabled != actual_enabled:
            self.user_prefs.auto_start_enabled = actual_enabled
            state = "enabled" if actual_enabled else "disabled"
            logger.debug(f"开机自启动状态已同步: {state}")
