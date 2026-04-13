"""Navigation, theming, and window-lifecycle helpers for the GUI shell."""

from __future__ import annotations

import contextlib
from typing import Any

from loguru import logger

from .ctk_compat import ctk
from .dialogs.exit_confirm import ExitConfirmDialog
from .styles.colors import ModernColors
from .utils.windows_integration import Windows11StyleHelper
from .widgets.animation_helper import TransitionManager
from .widgets.helpers import adjust_color_brightness
from .widgets.toast_notification import ToastNotification


class GUINavigationMixin:
    """Encapsulates page switching, theme propagation, and exit handling."""

    def _play_welcome_animation(self: Any) -> None:
        self._set_status("欢迎使用！", ModernColors.SUCCESS)

    def _on_window_close(self: Any) -> None:
        active_task = self._get_active_task_info()

        if active_task:
            dialog = ExitConfirmDialog(
                self.root,
                title="任务正在进行中",
                message="当前有任务正在运行，确定要退出吗？",
                task_info=active_task,
                icon="warning",
            )

            result = dialog.get()

            if result == "exit":
                logger.warning(f"用户强制退出，中断任务: {active_task}")
                self._force_exit()
            elif result == "minimize":
                logger.info("用户选择后台运行")
                self._on_close_to_tray()
            else:
                logger.debug("用户取消退出，继续任务")
        else:
            if self.user_prefs.minimize_to_tray:
                self._on_close_to_tray()
            else:
                self._safe_exit()

    def _get_active_task_info(self: Any) -> str | None:
        tasks: list[str] = []

        if self._batch_processing_active:
            if hasattr(self, "_batch_progress_tracker") and self._batch_progress_tracker:
                tracker = self._batch_progress_tracker
                tasks.append(f"批量处理 ({tracker.current}/{tracker.total} 篇)")
            else:
                tasks.append("批量处理中")

        if self._batch_export_active:
            if hasattr(self, "_export_progress_tracker") and self._export_progress_tracker:
                tracker = self._export_progress_tracker
                tasks.append(f"批量导出 ({tracker.current}/{tracker.total} 篇)")
            elif hasattr(self, "_zip_progress_tracker") and self._zip_progress_tracker:
                tracker = self._zip_progress_tracker
                tasks.append(f"ZIP打包 ({tracker.current}/{tracker.total} 篇)")
            else:
                tasks.append("批量导出中")

        if self._single_processing_active:
            tasks.append("单篇文章处理中")

        if tasks:
            return " | ".join(tasks)
        return None

    def _force_exit(self: Any) -> None:
        try:
            if self._log_handler_id:
                with contextlib.suppress(Exception):
                    logger.remove(self._log_handler_id)
            self.root.destroy()
        except Exception as exc:  # pragma: no cover - defensive GUI cleanup
            logger.error(f"强制退出时出错: {exc}")
            self.root.destroy()

    def _safe_exit(self: Any) -> None:
        try:
            if self._log_handler_id:
                with contextlib.suppress(Exception):
                    logger.remove(self._log_handler_id)

            logger.info("应用正常退出")
            self.root.destroy()
        except Exception as exc:  # pragma: no cover - defensive GUI cleanup
            logger.error(f"安全退出时出错: {exc}")
            self.root.destroy()

    def _on_close_to_tray(self: Any) -> None:
        self.root.withdraw()
        logger.info("窗口已最小化到系统托盘")

        try:
            if hasattr(self, "_toast_manager") and self._toast_manager:
                self._toast_manager.info("程序正在后台运行，双击托盘图标可恢复窗口")
            else:
                ToastNotification(
                    self.root,
                    "程序已最小化",
                    "程序正在后台运行\n双击托盘图标可恢复窗口",
                    "info",
                    duration_ms=3000,
                )
        except Exception:
            return None

    def _restore_from_tray(self: Any) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _refresh_summarizer_menus(self: Any) -> None:
        available_methods = [name for name, info in self._summarizer_info.items() if info.available]
        if not available_methods:
            available_methods = ["simple"]

        if hasattr(self, "method_menu"):
            self.method_menu.configure(values=available_methods)
            if self.method_var.get() not in available_methods:
                self.method_var.set(available_methods[0])

        if (
            hasattr(self, "batch_method_var")
            and self.batch_method_var.get() not in available_methods
        ):
            self.batch_method_var.set(available_methods[0])

    def _show_page(self: Any, page_id: str) -> None:
        from_page = self._current_page

        for frame in self._page_frames.values():
            frame.grid_forget()
        if page_id in self._page_frames:
            self._page_frames[page_id].grid(row=0, column=0, sticky="nsew")

        for pid, btn in self._nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
                    text_color="white",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
                )

        self._current_page = page_id

        with contextlib.suppress(Exception):
            self.event_bus.publish("navigate", from_page=from_page, to_page=page_id)

    def _show_page_animated(self: Any, page_id: str) -> None:
        if self._current_page == page_id:
            return None

        old_page = self._page_frames.get(self._current_page)
        new_page = self._page_frames.get(page_id)
        if not new_page:
            return None

        if self._is_low_memory_mode():
            self._show_page(page_id)
            return None

        page_order = [
            self.PAGE_HOME,
            self.PAGE_SINGLE,
            self.PAGE_BATCH,
            self.PAGE_HISTORY,
            self.PAGE_SETTINGS,
        ]
        try:
            old_idx = page_order.index(self._current_page)
            new_idx = page_order.index(page_id)
            direction = (
                TransitionManager.DIRECTION_LEFT
                if new_idx > old_idx
                else TransitionManager.DIRECTION_RIGHT
            )
        except ValueError:
            direction = TransitionManager.DIRECTION_LEFT

        self._update_nav_buttons_animated(page_id)

        old_page_id = self._current_page
        self._current_page = page_id

        def on_complete() -> None:
            page_names = {
                self.PAGE_HOME: "首页",
                self.PAGE_SINGLE: "单篇处理",
                self.PAGE_BATCH: "批量处理",
                self.PAGE_HISTORY: "历史记录",
                self.PAGE_SETTINGS: "设置",
            }
            page_name = page_names.get(page_id, page_id)
            self._animate_status_change(f"已切换到{page_name}")
            with contextlib.suppress(Exception):
                self.event_bus.publish("navigate", from_page=self._current_page, to_page=page_id)
            with contextlib.suppress(Exception):
                self.event_bus.publish("navigate", from_page=old_page_id, to_page=page_id)

        TransitionManager.slide_transition(
            self.root,
            self.content_area,
            old_page,
            new_page,
            direction=direction,
            on_complete=on_complete,
        )

    def _fade_in_page(self: Any, page_id: str) -> None:
        new_page = self._page_frames.get(page_id)
        if not new_page:
            return None

        old_page_id = self._current_page
        new_page.grid(row=0, column=0, sticky="nsew")
        self._update_nav_buttons_animated(page_id)
        self._current_page = page_id

        page_names = {
            self.PAGE_HOME: "首页",
            self.PAGE_SINGLE: "单篇处理",
            self.PAGE_BATCH: "批量处理",
            self.PAGE_HISTORY: "历史记录",
            self.PAGE_SETTINGS: "设置",
        }
        page_name = page_names.get(page_id, page_id)
        self._animate_status_change(f"已切换到{page_name}")
        with contextlib.suppress(Exception):
            self.event_bus.publish("navigate", from_page=old_page_id, to_page=page_id)

    def _update_nav_buttons_animated(self: Any, active_page_id: str) -> None:
        for pid, btn in self._nav_buttons.items():
            if pid == active_page_id:
                btn.configure(
                    fg_color=(ModernColors.LIGHT_ACCENT, ModernColors.DARK_ACCENT),
                    text_color="white",
                    hover_color=(ModernColors.LIGHT_ACCENT_HOVER, ModernColors.DARK_ACCENT_HOVER),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=(ModernColors.LIGHT_TEXT, ModernColors.DARK_TEXT),
                    hover_color=(ModernColors.LIGHT_HOVER_SUBTLE, ModernColors.DARK_HOVER_SUBTLE),
                )

    def _animate_status_change(self: Any, text: str) -> None:
        self._set_status(text, ModernColors.INFO)
        self.root.after(1500, lambda: self._set_status("就绪", ModernColors.SUCCESS))

    def _on_theme_change(self: Any, value: str) -> None:
        mode = "light" if value == "浅色" else "dark"
        ctk.set_appearance_mode(mode)
        self._appearance_mode = mode

        Windows11StyleHelper.update_titlebar_color(self.root, mode)
        self._broadcast_theme(mode)
        self._animate_status_change(f"已切换到{value}主题")

    def _broadcast_theme(self: Any, mode: str) -> None:
        for page in self._page_frames.values():
            self._update_widget_theme_recursive(page, mode)
        if hasattr(self, "sidebar") and self.sidebar:
            self._update_widget_theme_recursive(self.sidebar, mode)

    @staticmethod
    def _update_widget_theme_recursive(widget: Any, mode: str) -> None:
        if hasattr(widget, "update_theme") and callable(widget.update_theme):
            with contextlib.suppress(Exception):
                widget.update_theme(mode)

        for child in widget.winfo_children():
            GUINavigationMixin._update_widget_theme_recursive(child, mode)

    def _set_status(
        self: Any,
        text: str,
        color: str = ModernColors.SUCCESS,
        pulse: bool = False,
    ) -> None:
        self.status_label.configure(text=f"● {text}", text_color=color)
        if hasattr(self, "_pulse_animation_id") and self._pulse_animation_id:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._pulse_animation_id)
            self._pulse_animation_id = None

        if pulse:
            self._start_pulse_animation(color)

    def _start_pulse_animation(self: Any, base_color: str) -> None:
        self._pulse_phase = 0
        bright_color = adjust_color_brightness(base_color, 1.4)
        dim_color = adjust_color_brightness(base_color, 0.7)

        def pulse_step() -> None:
            if not hasattr(self, "_pulse_phase"):
                return None

            self._pulse_phase = (self._pulse_phase + 1) % 60

            import math

            t = (math.sin(self._pulse_phase * math.pi / 30) + 1) / 2
            try:
                br = int(bright_color.lstrip("#")[0:2], 16)
                bg = int(bright_color.lstrip("#")[2:4], 16)
                bb = int(bright_color.lstrip("#")[4:6], 16)
                dr = int(dim_color.lstrip("#")[0:2], 16)
                dg = int(dim_color.lstrip("#")[2:4], 16)
                db = int(dim_color.lstrip("#")[4:6], 16)

                r = int(dr + (br - dr) * t)
                g = int(dg + (bg - dg) * t)
                b = int(db + (bb - db) * t)
                current_color = f"#{r:02x}{g:02x}{b:02x}"
                self.status_label.configure(text_color=current_color)
            except Exception:
                pass

            self._pulse_animation_id = self.root.after(50, pulse_step)

        pulse_step()

    def _stop_pulse_animation(self: Any) -> None:
        if hasattr(self, "_pulse_animation_id") and self._pulse_animation_id:
            with contextlib.suppress(Exception):
                self.root.after_cancel(self._pulse_animation_id)
            self._pulse_animation_id = None

    def _refresh_availability(self: Any) -> None:
        self._summarizer_info = self._get_summarizer_info()
        self._exporter_info = self._get_exporter_info()
        if hasattr(self, "settings_page"):
            self.settings_page.update_summarizer_status_display()
        self._refresh_summarizer_menus()
        logger.info("已刷新服务状态")
        self._set_status("已刷新", ModernColors.SUCCESS)
