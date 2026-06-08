"""Models and defaults for keyboard shortcuts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Shortcut:
    """快捷键定义"""

    id: str
    name: str
    keys: str
    callback: Callable[[], None] | None = None
    group: str = "通用"
    description: str = ""
    enabled: bool = True


def default_shortcuts() -> list[Shortcut]:
    """Return built-in shortcuts without callbacks."""
    return [
        Shortcut(id="save", name="保存", keys="Ctrl+S", group="文件", description="保存当前文件"),
        Shortcut(id="open", name="打开", keys="Ctrl+O", group="文件", description="打开文件"),
        Shortcut(id="new", name="新建", keys="Ctrl+N", group="文件", description="新建文件"),
        Shortcut(id="undo", name="撤销", keys="Ctrl+Z", group="编辑", description="撤销上一步操作"),
        Shortcut(id="redo", name="重做", keys="Ctrl+Y", group="编辑", description="重做上一步操作"),
        Shortcut(id="copy", name="复制", keys="Ctrl+C", group="编辑", description="复制选中内容"),
        Shortcut(
            id="paste", name="粘贴", keys="Ctrl+V", group="编辑", description="粘贴剪贴板内容"
        ),
        Shortcut(id="cut", name="剪切", keys="Ctrl+X", group="编辑", description="剪切选中内容"),
        Shortcut(
            id="select_all", name="全选", keys="Ctrl+A", group="编辑", description="选中所有内容"
        ),
        Shortcut(id="find", name="查找", keys="Ctrl+F", group="编辑", description="打开查找对话框"),
        Shortcut(id="zoom_in", name="放大", keys="Ctrl+=", group="视图", description="放大界面"),
        Shortcut(id="zoom_out", name="缩小", keys="Ctrl+-", group="视图", description="缩小界面"),
        Shortcut(
            id="zoom_reset",
            name="重置缩放",
            keys="Ctrl+0",
            group="视图",
            description="重置界面缩放",
        ),
    ]


__all__ = ["Shortcut", "default_shortcuts"]
