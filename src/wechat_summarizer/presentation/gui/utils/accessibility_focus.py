"""Focus management for GUI accessibility helpers."""

from __future__ import annotations

import contextlib
import logging
import tkinter as tk
from typing import Any, cast

from .accessibility_models import (
    FocusableElement,
    FocusDirection,
    FocusRingStyle,
    FocusRingStyleDict,
)

logger = logging.getLogger(__name__)


class FocusManager:
    """焦点管理器"""

    _instance: FocusManager | None = None

    def __init__(self, root: tk.Tk):
        self.root = root
        self._elements: list[FocusableElement] = []
        self._groups: dict[str, list[FocusableElement]] = {}
        self._current_index = -1
        self._focus_ring_style: FocusRingStyleDict = FocusRingStyle.DEFAULT
        self._focus_ring_canvas: tk.Canvas | None = None
        self._trap_enabled = False
        self._trap_widgets: list[tk.Misc] = []
        self._bind_keyboard_events()

    @classmethod
    def get_instance(cls, root: tk.Tk | None = None) -> FocusManager:
        """获取单例实例"""
        if cls._instance is None:
            if root is None:
                raise ValueError("首次调用需要提供root参数")
            cls._instance = cls(root)
        return cls._instance

    def _bind_keyboard_events(self) -> None:
        self.root.bind_all("<Tab>", self._on_tab, add="+")
        self.root.bind_all("<Shift-Tab>", self._on_shift_tab, add="+")
        self.root.bind_all("<FocusIn>", self._on_focus_in, add="+")
        self.root.bind_all("<FocusOut>", self._on_focus_out, add="+")

    def register(
        self,
        widget: tk.Misc,
        tab_index: int = 0,
        group: str = "default",
        label: str = "",
        skip: bool = False,
    ) -> FocusableElement:
        """注册可聚焦元素"""
        element = FocusableElement(
            widget=widget, tab_index=tab_index, group=group, label=label, skip=skip
        )
        self._elements.append(element)
        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(element)
        self._sort_elements()
        return element

    def unregister(self, widget: tk.Misc) -> None:
        """注销元素"""
        self._elements = [element for element in self._elements if element.widget != widget]
        for group in self._groups.values():
            group[:] = [element for element in group if element.widget != widget]

    def _sort_elements(self) -> None:
        self._elements.sort(key=lambda element: (element.tab_index, self._elements.index(element)))
        for group in self._groups.values():
            group.sort(key=lambda element: element.tab_index)

    def _on_tab(self, event: Any) -> str:
        self._move_focus(FocusDirection.NEXT)
        return "break"

    def _on_shift_tab(self, event: Any) -> str:
        self._move_focus(FocusDirection.PREVIOUS)
        return "break"

    def _move_focus(self, direction: FocusDirection) -> None:
        focusable = [element for element in self._elements if self._can_focus(element)]
        if not focusable:
            return

        if self._trap_enabled and self._trap_widgets:
            focusable = [
                element
                for element in focusable
                if any(self._is_descendant(element.widget, widget) for widget in self._trap_widgets)
            ]

        if not focusable:
            return

        current_index = self._find_current_index(focusable)
        if direction == FocusDirection.NEXT:
            next_index = (current_index + 1) % len(focusable)
        elif direction == FocusDirection.PREVIOUS:
            next_index = (current_index - 1) % len(focusable)
        else:
            next_index = current_index

        self._set_focus(focusable[next_index].widget)

    def _can_focus(self, element: FocusableElement) -> bool:
        return not element.skip and element.widget.winfo_exists()

    def _find_current_index(self, focusable: list[FocusableElement]) -> int:
        current_widget = cast(tk.Misc | None, self.root.focus_get())
        for index, element in enumerate(focusable):
            if element.widget == current_widget or self._is_descendant(
                current_widget, element.widget
            ):
                return index
        return -1

    def _is_descendant(self, widget: tk.Misc | None, parent: tk.Misc) -> bool:
        """检查widget是否是parent的子组件"""
        if widget is None:
            return False

        while widget is not None:
            if widget == parent:
                return True
            widget = cast(tk.Misc | None, widget.master)

        return False

    def _set_focus(self, widget: tk.Misc) -> None:
        with contextlib.suppress(tk.TclError):
            widget.focus_set()

    def _on_focus_in(self, event: Any) -> None:
        self._draw_focus_ring(event.widget)

    def _on_focus_out(self, event: Any) -> None:
        self._clear_focus_ring()

    def _draw_focus_ring(self, widget: tk.Misc) -> None:
        self._clear_focus_ring()

        try:
            x = widget.winfo_rootx() - self.root.winfo_rootx()
            y = widget.winfo_rooty() - self.root.winfo_rooty()
            width = widget.winfo_width()
            height = widget.winfo_height()
            style = self._focus_ring_style
            offset = style["offset"]

            self._focus_ring_canvas = tk.Canvas(self.root, highlightthickness=0, bg="")
            rectangle_kwargs: dict[str, Any] = {
                "outline": style["color"],
                "width": style["width"],
            }
            if style["style"] == "dashed":
                rectangle_kwargs["dash"] = (4, 2)
            self._focus_ring_canvas.create_rectangle(
                offset,
                offset,
                width + offset * 2,
                height + offset * 2,
                **rectangle_kwargs,
            )
            self._focus_ring_canvas.place(
                x=x - offset,
                y=y - offset,
                width=width + offset * 4,
                height=height + offset * 4,
            )
            self._focus_ring_canvas.lower("all")
        except Exception as exc:
            logger.debug("绘制焦点轮廓失败: %s", exc)

    def _clear_focus_ring(self) -> None:
        if self._focus_ring_canvas:
            with contextlib.suppress(tk.TclError):
                self._focus_ring_canvas.destroy()
            self._focus_ring_canvas = None

    def set_focus_style(self, style: FocusRingStyleDict) -> None:
        """设置焦点样式"""
        self._focus_ring_style = style

    def enable_focus_trap(self, widgets: list[tk.Misc]) -> None:
        """启用焦点陷阱（用于模态框）"""
        self._trap_enabled = True
        self._trap_widgets = widgets

    def disable_focus_trap(self) -> None:
        """禁用焦点陷阱"""
        self._trap_enabled = False
        self._trap_widgets = []

    def focus_first(self, group: str = "default") -> None:
        """聚焦第一个元素"""
        focusable = [element for element in self._groups.get(group, []) if self._can_focus(element)]
        if focusable:
            self._set_focus(focusable[0].widget)

    def focus_last(self, group: str = "default") -> None:
        """聚焦最后一个元素"""
        focusable = [element for element in self._groups.get(group, []) if self._can_focus(element)]
        if focusable:
            self._set_focus(focusable[-1].widget)


__all__ = ["FocusManager"]
