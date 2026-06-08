"""Composition tests for split GUI glass components."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui.components import glass as glass_module
from wechat_summarizer.presentation.gui.components.glass import (
    GlassButton,
    GlassCard,
    GlassModal,
    LiquidGlassFrame,
    clamp_blur_radius,
    clamp_opacity,
    create_glass_card,
    create_glass_frame,
    resolve_glass_theme,
)
from wechat_summarizer.presentation.gui.components.glass_button import (
    GlassButton as SplitGlassButton,
)
from wechat_summarizer.presentation.gui.components.glass_card import (
    GlassCard as SplitGlassCard,
)
from wechat_summarizer.presentation.gui.components.glass_factory import (
    create_glass_card as split_create_glass_card,
)
from wechat_summarizer.presentation.gui.components.glass_factory import (
    create_glass_frame as split_create_glass_frame,
)
from wechat_summarizer.presentation.gui.components.glass_frame import (
    LiquidGlassFrame as SplitLiquidGlassFrame,
)
from wechat_summarizer.presentation.gui.components.glass_modal import (
    GlassModal as SplitGlassModal,
)
from wechat_summarizer.presentation.gui.components.glass_models import (
    MAX_GLASS_BLUR,
    MAX_GLASS_OPACITY,
    MIN_GLASS_BLUR,
    MIN_GLASS_OPACITY,
)


@pytest.mark.unit
def test_glass_module_keeps_compatibility_exports() -> None:
    assert glass_module.LiquidGlassFrame is SplitLiquidGlassFrame
    assert glass_module.GlassCard is SplitGlassCard
    assert glass_module.GlassButton is SplitGlassButton
    assert glass_module.GlassModal is SplitGlassModal
    assert glass_module.create_glass_frame is split_create_glass_frame
    assert glass_module.create_glass_card is split_create_glass_card
    assert LiquidGlassFrame is SplitLiquidGlassFrame
    assert GlassCard is SplitGlassCard
    assert GlassButton is SplitGlassButton
    assert GlassModal is SplitGlassModal
    assert create_glass_frame is split_create_glass_frame
    assert create_glass_card is split_create_glass_card


@pytest.mark.unit
def test_glass_models_preserve_limits_and_theme_resolution() -> None:
    dark = resolve_glass_theme("dark")
    light = resolve_glass_theme("light")

    assert LiquidGlassFrame.MIN_OPACITY == MIN_GLASS_OPACITY
    assert LiquidGlassFrame.MAX_OPACITY == MAX_GLASS_OPACITY
    assert LiquidGlassFrame.MIN_BLUR == MIN_GLASS_BLUR
    assert LiquidGlassFrame.MAX_BLUR == MAX_GLASS_BLUR
    assert clamp_opacity(-1.0) == MIN_GLASS_OPACITY
    assert clamp_opacity(2.0) == MAX_GLASS_OPACITY
    assert clamp_blur_radius(-10) == MIN_GLASS_BLUR
    assert clamp_blur_radius(999) == MAX_GLASS_BLUR
    assert dark.base == "#1e1e1e"
    assert light.base == "#ffffff"


@pytest.mark.unit
def test_glass_frame_class_preserves_animation_helpers_without_tk() -> None:
    frame = object.__new__(LiquidGlassFrame)
    frame._animated = True
    frame._animation_id = 1
    frame._base_color = "#1e1e1e"
    frame._animation_frame = 0

    assert frame._apply_opacity("#ffffff", 0.5) == "#ffffff"
    frame.stop_animation()
    assert frame._animated is False
    assert frame._animation_id is None

    frame.set_blur(999)
    assert frame._blur_radius == MAX_GLASS_BLUR


@pytest.mark.unit
def test_glass_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_animation.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_frame.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_card.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_button.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_modal.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/glass_factory.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
