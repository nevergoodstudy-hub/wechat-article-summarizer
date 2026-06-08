"""Persistence helpers for accessibility settings."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from typing import Any, cast

from loguru import logger

from .theme_models import AccessibilitySettings


def default_accessibility_config_file() -> str:
    """Return the default accessibility settings file path."""
    return os.path.join(os.path.expanduser("~"), ".wechat_summarizer", "accessibility.json")


def load_accessibility_settings(config_file: str) -> AccessibilitySettings:
    """加载可访问性设置"""
    try:
        if os.path.exists(config_file):
            with open(config_file, encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))

            return AccessibilitySettings(
                font_scale=data.get("font_scale", 1.0),
                contrast_mode=data.get("contrast_mode", "normal"),
                reduce_motion=data.get("reduce_motion", False),
                reduce_transparency=data.get("reduce_transparency", False),
            )
    except Exception as e:
        logger.warning(f"加载可访问性设置失败: {e}")

    return AccessibilitySettings()


def save_accessibility_settings(config_file: str, settings: AccessibilitySettings) -> None:
    """保存可访问性设置"""
    try:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2)
    except Exception as e:
        logger.warning(f"保存可访问性设置失败: {e}")


__all__ = [
    "default_accessibility_config_file",
    "load_accessibility_settings",
    "save_accessibility_settings",
]
