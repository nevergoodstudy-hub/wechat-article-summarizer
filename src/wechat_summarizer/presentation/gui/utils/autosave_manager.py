"""Autosave manager for GUI forms."""

from __future__ import annotations

import logging
import threading
import time
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from typing import Any

from .autosave_constants import DEFAULT_DEBOUNCE_MS
from .autosave_models import Draft, FormField
from .autosave_storage import DraftStorage

logger = logging.getLogger(__name__)


class AutoSaveManager:
    """表单自动保存管理器"""

    _instance: AutoSaveManager | None = None

    def __init__(self) -> None:
        self._storage: DraftStorage = DraftStorage()
        self._forms: dict[str, dict[str, FormField]] = {}
        self._debounce_timers: dict[str, threading.Timer] = {}
        self._debounce_delays: dict[str, int] = {}
        self._callbacks: dict[str, Callable[[Draft], None]] = {}
        self._enabled = True

    @classmethod
    def get_instance(cls) -> AutoSaveManager:
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_form(
        self,
        form_id: str,
        fields: list[FormField],
        debounce_ms: int = DEFAULT_DEBOUNCE_MS,
        on_restore: Callable[[Draft], None] | None = None,
    ) -> None:
        """注册表单"""
        self._forms[form_id] = {field.name: field for field in fields}
        self._debounce_delays[form_id] = debounce_ms

        if on_restore:
            self._callbacks[form_id] = on_restore

        for field in fields:
            self._bind_field_change(form_id, field)

    def _bind_field_change(self, form_id: str, field: FormField) -> None:
        widget = field.widget

        if isinstance(widget, (tk.Entry, ttk.Entry, tk.Text)):
            widget.bind("<KeyRelease>", lambda _event: self._on_field_change(form_id))
        elif isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", lambda _event: self._on_field_change(form_id))

    def _on_field_change(self, form_id: str) -> None:
        if not self._enabled:
            return

        if form_id in self._debounce_timers:
            self._debounce_timers[form_id].cancel()

        delay = self._debounce_delays.get(form_id, DEFAULT_DEBOUNCE_MS)
        timer = threading.Timer(delay / 1000.0, lambda: self._save_form(form_id))
        timer.start()
        self._debounce_timers[form_id] = timer

    def _save_form(self, form_id: str) -> None:
        if form_id not in self._forms:
            return

        data: dict[str, Any] = {}
        has_sensitive = False

        for name, field in self._forms[form_id].items():
            try:
                value = (
                    field.get_value() if field.get_value else self._get_widget_value(field.widget)
                )
                data[name] = value

                if field.sensitive:
                    has_sensitive = True
            except Exception as exc:
                logger.warning("获取字段值失败 (%s): %s", name, exc)

        draft = Draft(
            form_id=form_id,
            data=data,
            timestamp=time.time(),
            version=1,
            encrypted=has_sensitive,
        )
        self._storage.save(draft)
        logger.debug("自动保存表单: %s", form_id)

    def _get_widget_value(self, widget: tk.Widget) -> Any:
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            return widget.get()
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        if isinstance(widget, ttk.Combobox) or hasattr(widget, "get"):
            return widget.get()
        return None

    def _set_widget_value(self, widget: tk.Widget, value: Any) -> None:
        if isinstance(widget, (tk.Entry, ttk.Entry)):
            widget.delete(0, tk.END)
            widget.insert(0, str(value) if value else "")
        elif isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", str(value) if value else "")
        elif isinstance(widget, ttk.Combobox):
            widget.set(str(value) if value else "")

    def save_now(self, form_id: str) -> None:
        """立即保存"""
        if form_id in self._debounce_timers:
            self._debounce_timers[form_id].cancel()

        self._save_form(form_id)

    def has_draft(self, form_id: str) -> bool:
        """检查是否有草稿"""
        return self._storage.load_latest(form_id) is not None

    def get_draft(self, form_id: str) -> Draft | None:
        """获取最新草稿"""
        return self._storage.load_latest(form_id)

    def get_history(self, form_id: str) -> list[Draft]:
        """获取草稿历史"""
        return self._storage.load_history(form_id)

    def restore(self, form_id: str, draft: Draft | None = None) -> bool:
        """恢复草稿"""
        if draft is None:
            draft = self._storage.load_latest(form_id)

        if draft is None or form_id not in self._forms:
            return False

        for name, value in draft.data.items():
            if name in self._forms[form_id]:
                self._restore_field(name, self._forms[form_id][name], value)

        if form_id in self._callbacks:
            try:
                self._callbacks[form_id](draft)
            except Exception as exc:
                logger.error("恢复回调执行失败: %s", exc)

        return True

    def _restore_field(self, name: str, field: FormField, value: Any) -> None:
        try:
            if field.set_value:
                field.set_value(value)
            else:
                self._set_widget_value(field.widget, value)
        except Exception as exc:
            logger.warning("恢复字段值失败 (%s): %s", name, exc)

    def clear_draft(self, form_id: str) -> None:
        """清除草稿"""
        self._storage.delete(form_id)

    def enable(self) -> None:
        """启用自动保存"""
        self._enabled = True

    def disable(self) -> None:
        """禁用自动保存"""
        self._enabled = False

        for timer in self._debounce_timers.values():
            timer.cancel()
        self._debounce_timers.clear()

    def unregister_form(self, form_id: str) -> None:
        """注销表单"""
        if form_id in self._forms:
            del self._forms[form_id]

        if form_id in self._debounce_timers:
            self._debounce_timers[form_id].cancel()
            del self._debounce_timers[form_id]

        if form_id in self._debounce_delays:
            del self._debounce_delays[form_id]

        if form_id in self._callbacks:
            del self._callbacks[form_id]


__all__ = ["AutoSaveManager"]
