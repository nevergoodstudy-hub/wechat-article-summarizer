"""Composition tests for split GUI typography utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui.styles import typography as typography_module
from wechat_summarizer.presentation.gui.styles.typography import (
    ChineseFonts,
    FontFamily,
    FontSize,
    FontWeight,
    LetterSpacing,
    LineHeight,
    TextStyles,
    Typography,
    get_font,
    get_font_family,
    get_text_style,
)
from wechat_summarizer.presentation.gui.styles.typography_chinese import (
    ChineseFonts as SplitChineseFonts,
)
from wechat_summarizer.presentation.gui.styles.typography_families import (
    FontFamily as SplitFontFamily,
)
from wechat_summarizer.presentation.gui.styles.typography_manager import (
    Typography as SplitTypography,
)
from wechat_summarizer.presentation.gui.styles.typography_styles import (
    TextStyles as SplitTextStyles,
)
from wechat_summarizer.presentation.gui.styles.typography_styles import (
    get_font as split_get_font,
)
from wechat_summarizer.presentation.gui.styles.typography_styles import (
    get_font_family as split_get_font_family,
)
from wechat_summarizer.presentation.gui.styles.typography_styles import (
    get_text_style as split_get_text_style,
)
from wechat_summarizer.presentation.gui.styles.typography_tokens import (
    FontSize as SplitFontSize,
)
from wechat_summarizer.presentation.gui.styles.typography_tokens import (
    FontWeight as SplitFontWeight,
)
from wechat_summarizer.presentation.gui.styles.typography_tokens import (
    LetterSpacing as SplitLetterSpacing,
)
from wechat_summarizer.presentation.gui.styles.typography_tokens import (
    LineHeight as SplitLineHeight,
)


@pytest.mark.unit
def test_typography_module_keeps_compatibility_exports() -> None:
    assert typography_module.FontWeight is SplitFontWeight
    assert typography_module.FontSize is SplitFontSize
    assert typography_module.LineHeight is SplitLineHeight
    assert typography_module.LetterSpacing is SplitLetterSpacing
    assert typography_module.FontFamily is SplitFontFamily
    assert typography_module.Typography is SplitTypography
    assert typography_module.TextStyles is SplitTextStyles
    assert typography_module.ChineseFonts is SplitChineseFonts
    assert typography_module.get_font is split_get_font
    assert typography_module.get_font_family is split_get_font_family
    assert typography_module.get_text_style is split_get_text_style
    assert FontWeight is SplitFontWeight
    assert FontSize is SplitFontSize
    assert LineHeight is SplitLineHeight
    assert LetterSpacing is SplitLetterSpacing
    assert FontFamily is SplitFontFamily
    assert Typography is SplitTypography
    assert TextStyles is SplitTextStyles
    assert ChineseFonts is SplitChineseFonts
    assert get_font is split_get_font
    assert get_font_family is split_get_font_family
    assert get_text_style is split_get_text_style


@pytest.mark.unit
def test_typography_tokens_and_families_preserve_values() -> None:
    assert FontWeight.SEMI_BOLD.value == 600
    assert FontSize.BASE.value == 14
    assert LineHeight.RELAXED.value == 1.8
    assert LetterSpacing.WIDE.value == 0.025
    assert FontFamily.PRIMARY[:3] == ["Inter", "SF Pro Display", "Segoe UI"]
    assert FontFamily.COMBINED == FontFamily.PRIMARY + FontFamily.CJK


@pytest.mark.unit
def test_typography_manager_preserves_platform_fonts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from wechat_summarizer.presentation.gui.styles import typography_manager

    monkeypatch.setattr(typography_manager.platform, "system", lambda: "Windows")
    windows_typography = Typography()
    monkeypatch.setattr(typography_manager.platform, "system", lambda: "Darwin")
    mac_typography = Typography()
    monkeypatch.setattr(typography_manager.platform, "system", lambda: "Linux")
    linux_typography = Typography()

    assert windows_typography.get_primary_font() == "Segoe UI"
    assert windows_typography.get_monospace_font() == "Cascadia Code"
    assert mac_typography.get_primary_font() == "SF Pro Display"
    assert mac_typography.get_monospace_font() == "SF Mono"
    assert linux_typography.get_primary_font() == "Inter"
    assert linux_typography.get_monospace_font() == "JetBrains Mono"
    assert windows_typography.create_font_tuple(FontSize.MD, FontWeight.BOLD) == (
        "Segoe UI",
        16,
        "bold",
    )
    assert windows_typography.get_font_config(
        FontSize.SM, FontWeight.MEDIUM, LineHeight.NORMAL
    ) == {
        "size": 12,
        "weight": 500,
        "line_height": 1.5,
    }


@pytest.mark.unit
def test_typography_facade_helpers_preserve_text_styles() -> None:
    assert get_text_style(TextStyles.BUTTON_SMALL)[1:] == (12, "bold")
    assert get_font(FontSize.BASE, FontWeight.REGULAR)[1:] == (14, "normal")
    assert get_font(FontSize.BASE, FontWeight.REGULAR, monospace=True)[1:] == (14, "normal")
    assert get_font_family(monospace=True).startswith("JetBrains Mono")
    assert "Microsoft YaHei UI" in get_font_family(include_cjk=True)


@pytest.mark.unit
def test_chinese_fonts_fallback_is_cached() -> None:
    previous = ChineseFonts._detected_font
    try:
        ChineseFonts._detected_font = "Cached Font"
        assert ChineseFonts.get_best_font() == "Cached Font"
    finally:
        ChineseFonts._detected_font = previous


@pytest.mark.unit
def test_typography_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/styles/typography.py",
        repo_root / "src/wechat_summarizer/presentation/gui/styles/typography_tokens.py",
        repo_root / "src/wechat_summarizer/presentation/gui/styles/typography_families.py",
        repo_root / "src/wechat_summarizer/presentation/gui/styles/typography_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/styles/typography_styles.py",
        repo_root / "src/wechat_summarizer/presentation/gui/styles/typography_chinese.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
