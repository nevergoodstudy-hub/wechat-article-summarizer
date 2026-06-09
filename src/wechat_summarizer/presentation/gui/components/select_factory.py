"""Factory helpers for ModernSelect."""

from __future__ import annotations

from typing import Any

from .select_models import SelectMode, SelectOption
from .select_modern import ModernSelect


def create_select(
    master: Any,
    options: list[dict[str, Any]],
    mode: str = "single",
    placeholder: str = "请选择...",
    theme: str = "dark",
    **kwargs: Any,
) -> ModernSelect:
    """快速创建下拉选择器"""
    select_options = [
        SelectOption(
            value=option.get("value"),
            label=option.get("label", str(option.get("value"))),
            disabled=option.get("disabled", False),
        )
        for option in options
    ]
    select_mode = SelectMode.MULTIPLE if mode == "multiple" else SelectMode.SINGLE

    return ModernSelect(
        master,
        options=select_options,
        mode=select_mode,
        placeholder=placeholder,
        theme=theme,
        **kwargs,
    )


__all__ = ["create_select"]
