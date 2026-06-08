"""Composition tests for split progress and toast components."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.presentation.gui.components import progress as progress_module
from wechat_summarizer.presentation.gui.components import toast as toast_module
from wechat_summarizer.presentation.gui.components.progress import (
    CircularProgress,
    LinearProgress,
    StepProgress,
    create_circular_progress,
    create_linear_progress,
)
from wechat_summarizer.presentation.gui.components.progress_circular import (
    CircularProgress as SplitCircularProgress,
)
from wechat_summarizer.presentation.gui.components.progress_colors import (
    progress_colors_for_theme,
)
from wechat_summarizer.presentation.gui.components.progress_factory import (
    create_circular_progress as split_create_circular_progress,
)
from wechat_summarizer.presentation.gui.components.progress_factory import (
    create_linear_progress as split_create_linear_progress,
)
from wechat_summarizer.presentation.gui.components.progress_linear import (
    LinearProgress as SplitLinearProgress,
)
from wechat_summarizer.presentation.gui.components.progress_step import (
    StepProgress as SplitStepProgress,
)
from wechat_summarizer.presentation.gui.components.toast import (
    Toast,
    ToastManager,
    ToastType,
    get_toast_manager,
    init_toast_manager,
    show_error,
    show_info,
    show_success,
    show_toast,
    show_warning,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    get_toast_manager as split_get_toast_manager,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    init_toast_manager as split_init_toast_manager,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    show_error as split_show_error,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    show_info as split_show_info,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    show_success as split_show_success,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    show_toast as split_show_toast,
)
from wechat_summarizer.presentation.gui.components.toast_facade import (
    show_warning as split_show_warning,
)
from wechat_summarizer.presentation.gui.components.toast_item import Toast as SplitToast
from wechat_summarizer.presentation.gui.components.toast_manager import (
    ToastManager as SplitToastManager,
)
from wechat_summarizer.presentation.gui.components.toast_models import (
    ToastType as SplitToastType,
)
from wechat_summarizer.presentation.gui.components.toast_models import (
    toast_colors_for,
    toast_icon_for_type,
)


@pytest.mark.unit
def test_progress_module_keeps_compatibility_exports() -> None:
    assert progress_module.LinearProgress is SplitLinearProgress
    assert progress_module.CircularProgress is SplitCircularProgress
    assert progress_module.StepProgress is SplitStepProgress
    assert progress_module.create_linear_progress is split_create_linear_progress
    assert progress_module.create_circular_progress is split_create_circular_progress
    assert LinearProgress is SplitLinearProgress
    assert CircularProgress is SplitCircularProgress
    assert StepProgress is SplitStepProgress
    assert create_linear_progress is split_create_linear_progress
    assert create_circular_progress is split_create_circular_progress


@pytest.mark.unit
def test_progress_helpers_preserve_theme_and_bounds() -> None:
    dark = progress_colors_for_theme("dark")
    light = progress_colors_for_theme("light")

    assert dark.background != light.background
    assert dark.foreground != light.foreground
    assert dark.track != light.track


@pytest.mark.unit
def test_toast_module_keeps_compatibility_exports() -> None:
    assert toast_module.Toast is SplitToast
    assert toast_module.ToastManager is SplitToastManager
    assert toast_module.ToastType is SplitToastType
    assert toast_module.init_toast_manager is split_init_toast_manager
    assert toast_module.get_toast_manager is split_get_toast_manager
    assert toast_module.show_toast is split_show_toast
    assert toast_module.show_success is split_show_success
    assert toast_module.show_error is split_show_error
    assert toast_module.show_warning is split_show_warning
    assert toast_module.show_info is split_show_info
    assert Toast is SplitToast
    assert ToastManager is SplitToastManager
    assert ToastType is SplitToastType
    assert init_toast_manager is split_init_toast_manager
    assert get_toast_manager is split_get_toast_manager
    assert show_toast is split_show_toast
    assert show_success is split_show_success
    assert show_error is split_show_error
    assert show_warning is split_show_warning
    assert show_info is split_show_info


@pytest.mark.unit
def test_toast_models_preserve_icons_and_colors() -> None:
    assert ToastType.SUCCESS.value == "success"
    assert ToastType.ERROR.value == "error"
    assert ToastType.WARNING.value == "warning"
    assert ToastType.INFO.value == "info"
    assert toast_icon_for_type(ToastType.SUCCESS) == "✓"
    assert toast_icon_for_type(ToastType.ERROR) == "✕"
    assert toast_icon_for_type(ToastType.WARNING) == "⚠"
    assert toast_icon_for_type(ToastType.INFO) == "ℹ"

    success = toast_colors_for("dark", ToastType.SUCCESS)
    info = toast_colors_for("light", ToastType.INFO)

    assert success["icon"] == success["border"]
    assert info["icon"] == info["border"]
    assert success["bg"] != info["bg"]


@pytest.mark.unit
def test_progress_and_toast_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress_runtime.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress_colors.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress_linear.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress_circular.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress_step.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/progress_factory.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/toast.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/toast_runtime.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/toast_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/toast_item.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/toast_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/toast_facade.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
