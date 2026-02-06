"""统一间距规范 - 对齐 Windows 11 Fluent Design

提供:
- 标准间距常量 (XS/SM/MD/LG/XL/XXL)
- 圆角半径规范 (基于 ControlCornerRadius)
"""

from __future__ import annotations


class Spacing:
    """统一间距规范 - 对齐 Windows 11 Fluent Design"""
    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32
    XXL = 48
    # Windows 11 圆角半径 (基于官方 ControlCornerRadius 规范)
    RADIUS_SM = 4   # 小控件: 复选框、开关
    RADIUS_MD = 8   # 标准控件: 按钮、输入框
    RADIUS_LG = 12  # 卡片、面板
    RADIUS_XL = 16  # 大型容器、弹窗
    RADIUS_FULL = 9999  # 完全圆形
