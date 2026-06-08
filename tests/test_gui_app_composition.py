"""Composition tests for the thin GUI entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.bootstrap import gui as gui_bootstrap
from wechat_summarizer.presentation.gui import app as gui_app
from wechat_summarizer.presentation.gui.app_layout import GUILayoutMixin
from wechat_summarizer.presentation.gui.components import border as border_module
from wechat_summarizer.presentation.gui.components import modal as modal_module
from wechat_summarizer.presentation.gui.components.border import (
    Divider,
    GlowIntensity,
    GradientBorder,
    GradientDirection,
    create_divider,
    create_gradient_border,
)
from wechat_summarizer.presentation.gui.components.button import (
    ButtonGroup,
    ButtonSize,
    ButtonVariant,
    IconButton,
    ModernButton,
    create_button,
    create_icon_button,
)
from wechat_summarizer.presentation.gui.components.button import (
    RippleEffect as ButtonRippleEffect,
)
from wechat_summarizer.presentation.gui.components.button_factories import (
    create_button as split_create_button,
)
from wechat_summarizer.presentation.gui.components.button_factories import (
    create_icon_button as split_create_icon_button,
)
from wechat_summarizer.presentation.gui.components.button_group import (
    ButtonGroup as SplitButtonGroup,
)
from wechat_summarizer.presentation.gui.components.button_icon import (
    IconButton as SplitIconButton,
)
from wechat_summarizer.presentation.gui.components.button_models import (
    ButtonSize as SplitButtonSize,
)
from wechat_summarizer.presentation.gui.components.button_models import (
    ButtonVariant as SplitButtonVariant,
)
from wechat_summarizer.presentation.gui.components.button_models import (
    get_button_size_config,
    get_icon_button_size,
)
from wechat_summarizer.presentation.gui.components.button_modern import (
    ModernButton as SplitModernButton,
)
from wechat_summarizer.presentation.gui.components.button_ripple import (
    RippleEffect as SplitButtonRippleEffect,
)
from wechat_summarizer.presentation.gui.components.datagrid import (
    Column,
    DataGrid,
    VirtualScrollContainer,
)
from wechat_summarizer.presentation.gui.components.datagrid_data import DataGridDataMixin
from wechat_summarizer.presentation.gui.components.datagrid_header import DataGridHeaderMixin
from wechat_summarizer.presentation.gui.components.datagrid_rows import DataGridRowsMixin
from wechat_summarizer.presentation.gui.components.datagrid_toolbar import DataGridToolbarMixin
from wechat_summarizer.presentation.gui.components.datagrid_virtual import (
    VirtualScrollContainer as SplitVirtualScrollContainer,
)
from wechat_summarizer.presentation.gui.components.input import (
    ClearButton,
    FloatingLabel,
    ModernInput,
    ModernTextArea,
    PasswordInput,
    ValidationState,
    create_input,
    create_textarea,
)
from wechat_summarizer.presentation.gui.components.input_adornments import (
    ClearButton as SplitClearButton,
)
from wechat_summarizer.presentation.gui.components.input_adornments import (
    FloatingLabel as SplitFloatingLabel,
)
from wechat_summarizer.presentation.gui.components.input_factories import (
    create_input as split_create_input,
)
from wechat_summarizer.presentation.gui.components.input_factories import (
    create_textarea as split_create_textarea,
)
from wechat_summarizer.presentation.gui.components.input_modern import (
    ModernInput as SplitModernInput,
)
from wechat_summarizer.presentation.gui.components.input_password import (
    PasswordInput as SplitPasswordInput,
)
from wechat_summarizer.presentation.gui.components.input_state import (
    ValidationState as SplitValidationState,
)
from wechat_summarizer.presentation.gui.components.input_textarea import (
    ModernTextArea as SplitModernTextArea,
)
from wechat_summarizer.presentation.gui.components.modal import (
    AlertModal,
    ConfirmModal,
    Modal,
    ModalSize,
    show_alert,
    show_confirm,
    show_modal,
)
from wechat_summarizer.presentation.gui.components.modal_alert import (
    AlertModal as SplitAlertModal,
)
from wechat_summarizer.presentation.gui.components.modal_base import Modal as SplitModal
from wechat_summarizer.presentation.gui.components.modal_confirm import (
    ConfirmModal as SplitConfirmModal,
)
from wechat_summarizer.presentation.gui.components.modal_factory import (
    show_alert as split_show_alert,
)
from wechat_summarizer.presentation.gui.components.modal_factory import (
    show_confirm as split_show_confirm,
)
from wechat_summarizer.presentation.gui.components.modal_factory import (
    show_modal as split_show_modal,
)
from wechat_summarizer.presentation.gui.components.modal_models import (
    ModalSize as SplitModalSize,
)
from wechat_summarizer.presentation.gui.components.tab_indicator import (
    TabIndicator as SplitTabIndicator,
)
from wechat_summarizer.presentation.gui.components.tabs import (
    ModernTabs,
    TabIndicator,
    TabItem,
    TabPosition,
    create_tabs,
)
from wechat_summarizer.presentation.gui.components.tabs_button import TabsButtonMixin
from wechat_summarizer.presentation.gui.components.tabs_drag import TabsDragMixin
from wechat_summarizer.presentation.gui.components.tabs_factory import (
    create_tabs as split_create_tabs,
)
from wechat_summarizer.presentation.gui.components.tabs_models import (
    TabItem as SplitTabItem,
)
from wechat_summarizer.presentation.gui.components.tabs_models import (
    TabPosition as SplitTabPosition,
)
from wechat_summarizer.presentation.gui.components.tabs_modern import (
    ModernTabs as SplitModernTabs,
)
from wechat_summarizer.presentation.gui.components.tabs_selection import TabsSelectionMixin
from wechat_summarizer.presentation.gui.frames import (
    HomeActionCardsFrame,
    HomeInfoRowFrame,
    HomeTipBarFrame,
    HomeWelcomeFrame,
    SettingsApiKeysSection,
    SettingsExportSection,
    SettingsLanguageSection,
    SettingsPerformanceSection,
    SettingsQuickActionsFrame,
    SettingsSummarizerSection,
    SettingsSystemSection,
)
from wechat_summarizer.presentation.gui.pages.home_page import HomePage
from wechat_summarizer.presentation.gui.pages.settings_page import SettingsPage
from wechat_summarizer.presentation.gui.settings_api_actions import SettingsApiActionsMixin
from wechat_summarizer.presentation.gui.utils import autosave as autosave_module
from wechat_summarizer.presentation.gui.utils import microinteractions as microinteractions_module
from wechat_summarizer.presentation.gui.utils.autosave import (
    DEFAULT_DEBOUNCE_MS,
    DRAFT_EXPIRE_DAYS,
    MAX_DRAFT_SIZE,
    MAX_DRAFTS_PER_FORM,
    MAX_TOTAL_SIZE,
    AutoSaveManager,
    Draft,
    DraftStorage,
    FormField,
    RestoreDialog,
    SimpleEncryptor,
    check_and_restore,
)
from wechat_summarizer.presentation.gui.utils.autosave_constants import (
    DEFAULT_DEBOUNCE_MS as SPLIT_DEFAULT_DEBOUNCE_MS,
)
from wechat_summarizer.presentation.gui.utils.autosave_constants import (
    DRAFT_EXPIRE_DAYS as SPLIT_DRAFT_EXPIRE_DAYS,
)
from wechat_summarizer.presentation.gui.utils.autosave_constants import (
    MAX_DRAFT_SIZE as SPLIT_MAX_DRAFT_SIZE,
)
from wechat_summarizer.presentation.gui.utils.autosave_constants import (
    MAX_DRAFTS_PER_FORM as SPLIT_MAX_DRAFTS_PER_FORM,
)
from wechat_summarizer.presentation.gui.utils.autosave_constants import (
    MAX_TOTAL_SIZE as SPLIT_MAX_TOTAL_SIZE,
)
from wechat_summarizer.presentation.gui.utils.autosave_dialog import (
    RestoreDialog as SplitRestoreDialog,
)
from wechat_summarizer.presentation.gui.utils.autosave_dialog import (
    check_and_restore as split_check_and_restore,
)
from wechat_summarizer.presentation.gui.utils.autosave_encryptor import (
    SimpleEncryptor as SplitSimpleEncryptor,
)
from wechat_summarizer.presentation.gui.utils.autosave_manager import (
    AutoSaveManager as SplitAutoSaveManager,
)
from wechat_summarizer.presentation.gui.utils.autosave_models import (
    Draft as SplitDraft,
)
from wechat_summarizer.presentation.gui.utils.autosave_models import (
    FormField as SplitFormField,
)
from wechat_summarizer.presentation.gui.utils.autosave_storage import (
    DraftStorage as SplitDraftStorage,
)
from wechat_summarizer.presentation.gui.utils.microinteractions import (
    CollapseExpand,
    FocusRing,
    HoverEffect,
    MicroInteractions,
    PulseEffect,
    RippleEffect,
    ScaleEffect,
    SkeletonLoader,
    Spinner,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_feedback import (
    HoverEffect as SplitHoverEffect,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_feedback import (
    RippleEffect as SplitRippleEffect,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_feedback import (
    ScaleEffect as SplitScaleEffect,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_focus import (
    FocusRing as SplitFocusRing,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_loading import (
    SkeletonLoader as SplitSkeletonLoader,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_loading import (
    Spinner as SplitSpinner,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_manager import (
    MicroInteractions as SplitMicroInteractions,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_motion import (
    CollapseExpand as SplitCollapseExpand,
)
from wechat_summarizer.presentation.gui.utils.microinteractions_motion import (
    PulseEffect as SplitPulseEffect,
)


@pytest.mark.unit
def test_run_gui_uses_injected_dependencies(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}
    sentinel_container = object()
    sentinel_settings = object()

    class DummyMainWindow:
        def __init__(self, app_factory, *, container, settings):  # type: ignore[no-untyped-def]
            calls["app_factory"] = app_factory
            calls["container"] = container
            calls["settings"] = settings

        def run(self) -> None:
            calls["ran"] = True

    monkeypatch.setattr(gui_app, "CTK_AVAILABLE", True)
    monkeypatch.setattr(gui_app, "MainWindow", DummyMainWindow)

    gui_app.run_gui(container=sentinel_container, settings=sentinel_settings)

    assert calls["app_factory"] is gui_app.WechatSummarizerGUI
    assert calls["container"] is sentinel_container
    assert calls["settings"] is sentinel_settings
    assert calls["ran"] is True


@pytest.mark.unit
def test_run_gui_prints_install_hint_when_customtkinter_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(gui_app, "CTK_AVAILABLE", False)

    gui_app.run_gui(container=object(), settings=object())

    captured = capsys.readouterr()
    assert "customtkinter" in captured.out
    assert "pip install customtkinter" in captured.out


@pytest.mark.unit
def test_bootstrap_run_gui_assembles_infrastructure_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: dict[str, object] = {}
    sentinel_container = object()
    sentinel_settings = object()

    monkeypatch.setattr(gui_bootstrap, "get_container", lambda: sentinel_container)
    monkeypatch.setattr(gui_bootstrap, "get_settings", lambda: sentinel_settings)
    monkeypatch.setattr(
        gui_bootstrap,
        "run_gui_with_dependencies",
        lambda *, container, settings: calls.update({"container": container, "settings": settings}),
    )

    gui_bootstrap.run_gui()

    assert calls == {"container": sentinel_container, "settings": sentinel_settings}


@pytest.mark.unit
def test_gui_shell_layout_is_extracted_from_bootstrap() -> None:
    assert GUILayoutMixin in gui_app.WechatSummarizerGUI.__mro__
    assert "_build_ui" in GUILayoutMixin.__dict__
    assert "_build_sidebar" in GUILayoutMixin.__dict__
    assert "_build_log_panel" in GUILayoutMixin.__dict__
    assert "_build_ui" not in gui_app.GUIBootstrapMixin.__dict__
    assert "_build_sidebar" not in gui_app.GUIBootstrapMixin.__dict__


@pytest.mark.unit
def test_home_page_delegates_dashboard_sections_to_frames() -> None:
    assert "_build_welcome" not in HomePage.__dict__
    assert "_build_action_cards" not in HomePage.__dict__
    assert "_build_status_overview" not in HomePage.__dict__
    assert "_build_recent_records" not in HomePage.__dict__
    assert "_build_tip_bar" not in HomePage.__dict__
    assert "_build" in HomeWelcomeFrame.__dict__
    assert "_build" in HomeActionCardsFrame.__dict__
    assert "_build" in HomeInfoRowFrame.__dict__
    assert "_build" in HomeTipBarFrame.__dict__


@pytest.mark.unit
def test_home_dashboard_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/pages/home_page.py",
        repo_root / "src/wechat_summarizer/presentation/gui/frames/home_dashboard.py",
        repo_root / "src/wechat_summarizer/presentation/gui/frames/home_info.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_settings_page_delegates_preference_sections_to_frames() -> None:
    assert "_build" in SettingsSummarizerSection.__dict__
    assert "_build" in SettingsApiKeysSection.__dict__
    assert "_build" in SettingsExportSection.__dict__
    assert "_build" in SettingsSystemSection.__dict__
    assert "_build" in SettingsPerformanceSection.__dict__
    assert "_build" in SettingsLanguageSection.__dict__
    assert "_build" in SettingsQuickActionsFrame.__dict__
    assert "update_status" in SettingsSummarizerSection.__dict__
    assert SettingsApiActionsMixin in SettingsPage.__mro__
    assert "_build_provider_row" not in SettingsPage.__dict__


@pytest.mark.unit
def test_settings_gui_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/pages/settings_page.py",
        repo_root / "src/wechat_summarizer/presentation/gui/frames/settings_service.py",
        repo_root / "src/wechat_summarizer/presentation/gui/frames/settings_preferences.py",
        repo_root / "src/wechat_summarizer/presentation/gui/settings_api_actions.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_border_module_keeps_compatibility_exports() -> None:
    assert border_module.GradientBorder is GradientBorder
    assert border_module.Divider is Divider
    assert border_module.GradientDirection is GradientDirection
    assert border_module.GlowIntensity is GlowIntensity
    assert border_module.create_gradient_border is create_gradient_border
    assert border_module.create_divider is create_divider
    assert border_module._validate_hex_color("#abc") is True
    assert border_module.validate_hex_color("#aabbcc") is True
    assert border_module._hex_to_rgb("#abc") == (170, 187, 204)
    assert border_module.hex_to_rgb("#11223344") == (17, 34, 51)
    assert border_module._rgb_to_hex((300, -1, 16)) == "#ff0010"
    assert border_module.interpolate_color("#000000", "#ffffff", 0.5) == "#7f7f7f"
    assert "GradientBorder" in border_module.__all__


@pytest.mark.unit
def test_border_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/border.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/border_utils.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/gradient_border.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/gradient_border_draw.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/divider.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_button_module_keeps_compatibility_exports() -> None:
    assert ModernButton is SplitModernButton
    assert IconButton is SplitIconButton
    assert ButtonGroup is SplitButtonGroup
    assert ButtonVariant is SplitButtonVariant
    assert ButtonSize is SplitButtonSize
    assert ButtonRippleEffect is SplitButtonRippleEffect
    assert create_button is split_create_button
    assert create_icon_button is split_create_icon_button
    assert ButtonVariant.PRIMARY.value == "primary"
    assert ButtonSize.MEDIUM.value == "medium"
    assert get_button_size_config(ButtonSize.LARGE)["height"] == 44
    assert get_icon_button_size(ButtonSize.SMALL) == 32


@pytest.mark.unit
def test_button_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/button.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_ripple.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_modern.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_icon.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_group.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/button_factories.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_datagrid_keeps_compatibility_exports_and_composition() -> None:
    column = Column(key="title", label="标题", width=120)

    assert column.key == "title"
    assert column.sortable is True
    assert VirtualScrollContainer is SplitVirtualScrollContainer
    assert DataGridToolbarMixin in DataGrid.__mro__
    assert DataGridHeaderMixin in DataGrid.__mro__
    assert DataGridRowsMixin in DataGrid.__mro__
    assert DataGridDataMixin in DataGrid.__mro__
    assert DataGrid.MAX_ROWS == 50000


@pytest.mark.unit
def test_datagrid_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_virtual.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_header.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_rows.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_toolbar.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_data.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/datagrid_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_input_module_keeps_compatibility_exports() -> None:
    assert ModernInput is SplitModernInput
    assert ModernTextArea is SplitModernTextArea
    assert PasswordInput is SplitPasswordInput
    assert ValidationState is SplitValidationState
    assert FloatingLabel is SplitFloatingLabel
    assert ClearButton is SplitClearButton
    assert create_input is split_create_input
    assert create_textarea is split_create_textarea
    assert ValidationState.ERROR.value == "error"


@pytest.mark.unit
def test_input_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/input.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_state.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_adornments.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_modern.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_textarea.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_password.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/input_factories.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_modal_module_keeps_compatibility_exports() -> None:
    assert modal_module.Modal is SplitModal
    assert modal_module.ConfirmModal is SplitConfirmModal
    assert modal_module.AlertModal is SplitAlertModal
    assert modal_module.ModalSize is SplitModalSize
    assert modal_module.show_modal is split_show_modal
    assert modal_module.show_confirm is split_show_confirm
    assert modal_module.show_alert is split_show_alert
    assert Modal is SplitModal
    assert ConfirmModal is SplitConfirmModal
    assert AlertModal is SplitAlertModal
    assert ModalSize is SplitModalSize
    assert show_modal is split_show_modal
    assert show_confirm is split_show_confirm
    assert show_alert is split_show_alert
    assert Modal._modal_stack is SplitModal._modal_stack
    assert ModalSize.SMALL.value == (400, 200)
    assert ModalSize.FULLSCREEN.value == (0, 0)


@pytest.mark.unit
def test_modal_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal_base.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal_confirm.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal_alert.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/modal_factory.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_tabs_module_keeps_compatibility_exports_and_composition() -> None:
    assert ModernTabs is SplitModernTabs
    assert TabIndicator is SplitTabIndicator
    assert TabItem is SplitTabItem
    assert TabPosition is SplitTabPosition
    assert create_tabs is split_create_tabs
    assert TabsButtonMixin in ModernTabs.__mro__
    assert TabsSelectionMixin in ModernTabs.__mro__
    assert TabsDragMixin in ModernTabs.__mro__
    assert ModernTabs.MAX_TABS == 50
    assert TabPosition.TOP.value == "top"


@pytest.mark.unit
def test_tabs_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tab_indicator.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_button.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_selection.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_drag.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_modern.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/tabs_factory.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_microinteractions_module_keeps_compatibility_exports() -> None:
    assert microinteractions_module.RippleEffect is SplitRippleEffect
    assert microinteractions_module.ScaleEffect is SplitScaleEffect
    assert microinteractions_module.HoverEffect is SplitHoverEffect
    assert microinteractions_module.SkeletonLoader is SplitSkeletonLoader
    assert microinteractions_module.Spinner is SplitSpinner
    assert microinteractions_module.PulseEffect is SplitPulseEffect
    assert microinteractions_module.CollapseExpand is SplitCollapseExpand
    assert microinteractions_module.FocusRing is SplitFocusRing
    assert microinteractions_module.MicroInteractions is SplitMicroInteractions
    assert RippleEffect is SplitRippleEffect
    assert ScaleEffect is SplitScaleEffect
    assert HoverEffect is SplitHoverEffect
    assert SkeletonLoader is SplitSkeletonLoader
    assert Spinner is SplitSpinner
    assert PulseEffect is SplitPulseEffect
    assert CollapseExpand is SplitCollapseExpand
    assert FocusRing is SplitFocusRing
    assert MicroInteractions is SplitMicroInteractions


@pytest.mark.unit
def test_microinteractions_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions_feedback.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions_loading.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions_motion.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions_focus.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/microinteractions_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_autosave_module_keeps_compatibility_exports() -> None:
    assert autosave_module.AutoSaveManager is SplitAutoSaveManager
    assert autosave_module.Draft is SplitDraft
    assert autosave_module.FormField is SplitFormField
    assert autosave_module.DraftStorage is SplitDraftStorage
    assert autosave_module.RestoreDialog is SplitRestoreDialog
    assert autosave_module.SimpleEncryptor is SplitSimpleEncryptor
    assert autosave_module.check_and_restore is split_check_and_restore
    assert AutoSaveManager is SplitAutoSaveManager
    assert Draft is SplitDraft
    assert FormField is SplitFormField
    assert DraftStorage is SplitDraftStorage
    assert RestoreDialog is SplitRestoreDialog
    assert SimpleEncryptor is SplitSimpleEncryptor
    assert check_and_restore is split_check_and_restore
    assert SPLIT_MAX_DRAFT_SIZE == MAX_DRAFT_SIZE
    assert SPLIT_MAX_TOTAL_SIZE == MAX_TOTAL_SIZE
    assert SPLIT_MAX_DRAFTS_PER_FORM == MAX_DRAFTS_PER_FORM
    assert SPLIT_DRAFT_EXPIRE_DAYS == DRAFT_EXPIRE_DAYS
    assert SPLIT_DEFAULT_DEBOUNCE_MS == DEFAULT_DEBOUNCE_MS


@pytest.mark.unit
def test_autosave_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_constants.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_encryptor.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_storage.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_dialog.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/autosave_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
