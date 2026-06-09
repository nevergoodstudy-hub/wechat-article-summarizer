"""Composition tests for split GUI gradient utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui.utils import gradient as gradient_module
from wechat_summarizer.presentation.gui.utils.gradient import (
    EasingFunction,
    GradientAnimator,
    GradientConfig,
    GradientManager,
    GradientStop,
    GradientType,
    create_gradient,
    interpolate,
)
from wechat_summarizer.presentation.gui.utils.gradient_animator import (
    GradientAnimator as SplitGradientAnimator,
)
from wechat_summarizer.presentation.gui.utils.gradient_facade import (
    create_gradient as split_create_gradient,
)
from wechat_summarizer.presentation.gui.utils.gradient_facade import (
    interpolate as split_interpolate,
)
from wechat_summarizer.presentation.gui.utils.gradient_manager import (
    GradientManager as SplitGradientManager,
)
from wechat_summarizer.presentation.gui.utils.gradient_models import (
    EasingFunction as SplitEasingFunction,
)
from wechat_summarizer.presentation.gui.utils.gradient_models import (
    GradientConfig as SplitGradientConfig,
)
from wechat_summarizer.presentation.gui.utils.gradient_models import (
    GradientStop as SplitGradientStop,
)
from wechat_summarizer.presentation.gui.utils.gradient_models import (
    GradientType as SplitGradientType,
)


@pytest.mark.unit
def test_gradient_module_keeps_compatibility_exports() -> None:
    assert gradient_module.GradientType is SplitGradientType
    assert gradient_module.EasingFunction is SplitEasingFunction
    assert gradient_module.GradientStop is SplitGradientStop
    assert gradient_module.GradientConfig is SplitGradientConfig
    assert gradient_module.GradientManager is SplitGradientManager
    assert gradient_module.GradientAnimator is SplitGradientAnimator
    assert gradient_module.create_gradient is split_create_gradient
    assert gradient_module.interpolate is split_interpolate
    assert GradientType is SplitGradientType
    assert EasingFunction is SplitEasingFunction
    assert GradientStop is SplitGradientStop
    assert GradientConfig is SplitGradientConfig
    assert GradientManager is SplitGradientManager
    assert GradientAnimator is SplitGradientAnimator
    assert create_gradient is split_create_gradient
    assert interpolate is split_interpolate


@pytest.mark.unit
def test_gradient_models_preserve_bounds_and_values() -> None:
    stop = GradientStop("#ffffff", 2.0)
    config = GradientConfig(angle=725.0)

    assert GradientType.LINEAR.value == "linear"
    assert GradientType.RADIAL.value == "radial"
    assert GradientType.CONIC.value == "conic"
    assert EasingFunction.EASE_IN_OUT.value == "ease_in_out"
    assert stop.position == 1.0
    assert config.angle == 5.0
    assert config.stops == []


@pytest.mark.unit
def test_gradient_manager_preserves_color_generation_behavior() -> None:
    manager = GradientManager()
    config = GradientConfig(
        stops=[
            GradientStop("#000000", 0.0),
            GradientStop("#ffffff", 1.0),
        ]
    )

    assert manager.rgb_to_hex(-10, 128, 999) == "#0080ff"
    assert manager.interpolate_color("#000000", "#ffffff", 0.5) == "#7f7f7f"
    assert manager.create_linear_gradient(["#000000", "#ffffff"], steps=3) == [
        "#000000",
        "#7f7f7f",
        "#ffffff",
    ]
    assert manager.create_radial_gradient(["#000000", "#ffffff"], steps=2) == [
        "#000000",
        "#ffffff",
    ]
    assert manager.get_color_at_position(config, 0.5) == "#7f7f7f"


@pytest.mark.unit
def test_gradient_animator_preserves_limits_and_color_flow() -> None:
    animator = GradientAnimator(fps=999)
    flow_id = animator.create_color_flow_animation(
        ["#000000", "#ffffff"],
        duration=0.1,
        loop=False,
        easing=EasingFunction.LINEAR,
    )

    animator._animations[flow_id]["start_time"] = 0.0

    assert animator.fps == GradientAnimator.MAX_FPS
    assert GradientAnimator.apply_easing(0.5, EasingFunction.EASE_IN) == 0.25
    assert GradientAnimator.apply_easing(0.5, EasingFunction.EASE_OUT) == 0.75
    assert isinstance(animator.get_current_color(flow_id), str)
    animator.stop_animation(flow_id)
    assert animator.get_current_color(flow_id) is None


@pytest.mark.unit
def test_gradient_facade_preserves_helpers() -> None:
    assert interpolate("#000000", "#ffffff", 0.5) == "#7f7f7f"
    assert create_gradient(["#000000", "#ffffff"], steps=2) == ["#000000", "#ffffff"]
    assert create_gradient(["#000000", "#ffffff"], gradient_type="radial", steps=2) == [
        "#000000",
        "#ffffff",
    ]


@pytest.mark.unit
def test_gradient_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/gradient.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/gradient_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/gradient_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/gradient_animator.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/gradient_facade.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
