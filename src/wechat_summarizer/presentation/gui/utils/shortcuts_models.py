"""Models and defaults for keyboard shortcuts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .i18n import tr


@dataclass
class Shortcut:
    """快捷键定义"""

    id: str
    name: str
    keys: str
    callback: Callable[[], None] | None = None
    group: str = tr("通用")
    description: str = ""
    enabled: bool = True


def default_shortcuts() -> list[Shortcut]:
    """Return built-in shortcuts without callbacks."""
    return [
        Shortcut(
            id="save",
            name=tr("保存"),
            keys="Ctrl+S",
            group=tr("文件"),
            description=tr("保存当前文件"),
        ),
        Shortcut(
            id="open", name=tr("打开"), keys="Ctrl+O", group=tr("文件"), description=tr("打开文件")
        ),
        Shortcut(
            id="new", name=tr("新建"), keys="Ctrl+N", group=tr("文件"), description=tr("新建文件")
        ),
        Shortcut(
            id="undo",
            name=tr("撤销"),
            keys="Ctrl+Z",
            group=tr("编辑"),
            description=tr("撤销上一步操作"),
        ),
        Shortcut(
            id="redo",
            name=tr("重做"),
            keys="Ctrl+Y",
            group=tr("编辑"),
            description=tr("重做上一步操作"),
        ),
        Shortcut(
            id="copy",
            name=tr("复制"),
            keys="Ctrl+C",
            group=tr("编辑"),
            description=tr("复制选中内容"),
        ),
        Shortcut(
            id="paste",
            name=tr("粘贴"),
            keys="Ctrl+V",
            group=tr("编辑"),
            description=tr("粘贴剪贴板内容"),
        ),
        Shortcut(
            id="cut",
            name=tr("剪切"),
            keys="Ctrl+X",
            group=tr("编辑"),
            description=tr("剪切选中内容"),
        ),
        Shortcut(
            id="select_all",
            name=tr("全选"),
            keys="Ctrl+A",
            group=tr("编辑"),
            description=tr("选中所有内容"),
        ),
        Shortcut(
            id="find",
            name=tr("查找"),
            keys="Ctrl+F",
            group=tr("编辑"),
            description=tr("打开查找对话框"),
        ),
        Shortcut(
            id="zoom_in",
            name=tr("放大"),
            keys="Ctrl+=",
            group=tr("视图"),
            description=tr("放大界面"),
        ),
        Shortcut(
            id="zoom_out",
            name=tr("缩小"),
            keys="Ctrl+-",
            group=tr("视图"),
            description=tr("缩小界面"),
        ),
        Shortcut(
            id="zoom_reset",
            name=tr("重置缩放"),
            keys="Ctrl+0",
            group=tr("视图"),
            description=tr("重置界面缩放"),
        ),
    ]


__all__ = ["Shortcut", "default_shortcuts"]
