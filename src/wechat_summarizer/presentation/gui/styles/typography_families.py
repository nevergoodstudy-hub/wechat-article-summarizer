"""Typography family stacks."""

from __future__ import annotations


class FontFamily:
    """Font family fallbacks ordered by preference."""

    PRIMARY = [
        "Inter",
        "SF Pro Display",
        "Segoe UI",
        "-apple-system",
        "BlinkMacSystemFont",
        "Helvetica Neue",
        "Arial",
        "sans-serif",
    ]

    MONOSPACE = [
        "JetBrains Mono",
        "Fira Code",
        "SF Mono",
        "Cascadia Code",
        "Menlo",
        "Monaco",
        "Consolas",
        "Courier New",
        "monospace",
    ]

    CJK = [
        "PingFang SC",
        "Microsoft YaHei UI",
        "Microsoft YaHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "SimHei",
        "sans-serif",
    ]

    COMBINED = PRIMARY + CJK


__all__ = ["FontFamily"]
