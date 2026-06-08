"""Composition tests for the thin GUI entrypoint."""

from __future__ import annotations

from pathlib import Path

import pytest

from wechat_summarizer.bootstrap import gui as gui_bootstrap
from wechat_summarizer.domain.entities import Article
from wechat_summarizer.domain.value_objects import ArticleContent, ArticleURL
from wechat_summarizer.presentation.gui import app as gui_app
from wechat_summarizer.presentation.gui.app_layout import GUILayoutMixin
from wechat_summarizer.presentation.gui.assets import icons as icons_module
from wechat_summarizer.presentation.gui.assets.icons import (
    ICON_PATHS,
    IconManager,
    IconSize,
    IconStyle,
    SVGPathParser,
    get_icon,
    get_icon_tk,
    list_icons,
)
from wechat_summarizer.presentation.gui.assets.icons_facade import (
    get_icon as split_get_icon,
)
from wechat_summarizer.presentation.gui.assets.icons_facade import (
    get_icon_tk as split_get_icon_tk,
)
from wechat_summarizer.presentation.gui.assets.icons_facade import (
    list_icons as split_list_icons,
)
from wechat_summarizer.presentation.gui.assets.icons_manager import (
    IconManager as SplitIconManager,
)
from wechat_summarizer.presentation.gui.assets.icons_models import (
    IconSize as SplitIconSize,
)
from wechat_summarizer.presentation.gui.assets.icons_models import (
    IconStyle as SplitIconStyle,
)
from wechat_summarizer.presentation.gui.assets.icons_parser import (
    SVGPathParser as SplitSVGPathParser,
)
from wechat_summarizer.presentation.gui.assets.icons_paths import (
    ICON_PATHS as SPLIT_ICON_PATHS,
)
from wechat_summarizer.presentation.gui.components import border as border_module
from wechat_summarizer.presentation.gui.components import card as card_module
from wechat_summarizer.presentation.gui.components import modal as modal_module
from wechat_summarizer.presentation.gui.components import select as select_module
from wechat_summarizer.presentation.gui.components import sidebar as sidebar_module
from wechat_summarizer.presentation.gui.components import virtuallist as virtuallist_module
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
from wechat_summarizer.presentation.gui.components.card import (
    _CTK_AVAILABLE as CARD_CTK_AVAILABLE,
)
from wechat_summarizer.presentation.gui.components.card import (
    ActionCard,
    CardStyle,
    ContentCard,
    CornerRadius,
    ModernCard,
    ShadowDepth,
    StatCard,
    create_card,
    create_content_card,
)
from wechat_summarizer.presentation.gui.components.card import ctk as card_ctk
from wechat_summarizer.presentation.gui.components.card_action import (
    ActionCard as SplitActionCard,
)
from wechat_summarizer.presentation.gui.components.card_base import ModernCard as SplitModernCard
from wechat_summarizer.presentation.gui.components.card_compat import (
    CTK_AVAILABLE as SPLIT_CARD_CTK_AVAILABLE,
)
from wechat_summarizer.presentation.gui.components.card_compat import ctk as split_card_ctk
from wechat_summarizer.presentation.gui.components.card_content import (
    ContentCard as SplitContentCard,
)
from wechat_summarizer.presentation.gui.components.card_factory import (
    create_card as split_create_card,
)
from wechat_summarizer.presentation.gui.components.card_factory import (
    create_content_card as split_create_content_card,
)
from wechat_summarizer.presentation.gui.components.card_models import (
    CardStyle as SplitCardStyle,
)
from wechat_summarizer.presentation.gui.components.card_models import (
    CornerRadius as SplitCornerRadius,
)
from wechat_summarizer.presentation.gui.components.card_models import (
    ShadowDepth as SplitShadowDepth,
)
from wechat_summarizer.presentation.gui.components.card_stat import StatCard as SplitStatCard
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
from wechat_summarizer.presentation.gui.components.select import (
    ModernSelect,
    SelectMode,
    SelectOption,
    create_select,
)
from wechat_summarizer.presentation.gui.components.select_dropdown import SelectDropdownMixin
from wechat_summarizer.presentation.gui.components.select_factory import (
    create_select as split_create_select,
)
from wechat_summarizer.presentation.gui.components.select_models import (
    SelectMode as SplitSelectMode,
)
from wechat_summarizer.presentation.gui.components.select_models import (
    SelectOption as SplitSelectOption,
)
from wechat_summarizer.presentation.gui.components.select_modern import (
    ModernSelect as SplitModernSelect,
)
from wechat_summarizer.presentation.gui.components.sidebar import (
    CollapsibleSidebar,
    NavItem,
    Tooltip,
    default_sidebar_state_file,
    resolve_sidebar_state_file,
)
from wechat_summarizer.presentation.gui.components.sidebar_animation import (
    SidebarAnimationMixin,
)
from wechat_summarizer.presentation.gui.components.sidebar_core import (
    CollapsibleSidebar as SplitCollapsibleSidebar,
)
from wechat_summarizer.presentation.gui.components.sidebar_items import SidebarItemsMixin
from wechat_summarizer.presentation.gui.components.sidebar_models import NavItem as SplitNavItem
from wechat_summarizer.presentation.gui.components.sidebar_models import clamp_badge
from wechat_summarizer.presentation.gui.components.sidebar_state import (
    SidebarStateMixin,
)
from wechat_summarizer.presentation.gui.components.sidebar_state import (
    default_sidebar_state_file as split_default_sidebar_state_file,
)
from wechat_summarizer.presentation.gui.components.sidebar_state import (
    resolve_sidebar_state_file as split_resolve_sidebar_state_file,
)
from wechat_summarizer.presentation.gui.components.sidebar_tooltip import Tooltip as SplitTooltip
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
from wechat_summarizer.presentation.gui.components.virtuallist import (
    MAX_ITEM_HEIGHT as VIRTUAL_LIST_MAX_ITEM_HEIGHT,
)
from wechat_summarizer.presentation.gui.components.virtuallist import (
    MAX_ITEMS as VIRTUAL_LIST_MAX_ITEMS,
)
from wechat_summarizer.presentation.gui.components.virtuallist import (
    MIN_ITEM_HEIGHT as VIRTUAL_LIST_MIN_ITEM_HEIGHT,
)
from wechat_summarizer.presentation.gui.components.virtuallist import (
    RENDER_TIMEOUT_MS as VIRTUAL_LIST_RENDER_TIMEOUT_MS,
)
from wechat_summarizer.presentation.gui.components.virtuallist import (
    SCROLL_THROTTLE_MS as VIRTUAL_LIST_SCROLL_THROTTLE_MS,
)
from wechat_summarizer.presentation.gui.components.virtuallist import VirtualItem, VirtualList
from wechat_summarizer.presentation.gui.components.virtuallist_models import (
    MAX_ITEM_HEIGHT as SPLIT_VIRTUAL_LIST_MAX_ITEM_HEIGHT,
)
from wechat_summarizer.presentation.gui.components.virtuallist_models import (
    MAX_ITEMS as SPLIT_VIRTUAL_LIST_MAX_ITEMS,
)
from wechat_summarizer.presentation.gui.components.virtuallist_models import (
    MIN_ITEM_HEIGHT as SPLIT_VIRTUAL_LIST_MIN_ITEM_HEIGHT,
)
from wechat_summarizer.presentation.gui.components.virtuallist_models import (
    RENDER_TIMEOUT_MS as SPLIT_VIRTUAL_LIST_RENDER_TIMEOUT_MS,
)
from wechat_summarizer.presentation.gui.components.virtuallist_models import (
    SCROLL_THROTTLE_MS as SPLIT_VIRTUAL_LIST_SCROLL_THROTTLE_MS,
)
from wechat_summarizer.presentation.gui.components.virtuallist_models import (
    VirtualItem as SplitVirtualItem,
)
from wechat_summarizer.presentation.gui.components.virtuallist_render import VirtualListRenderMixin
from wechat_summarizer.presentation.gui.dialogs import word_preview as word_preview_module
from wechat_summarizer.presentation.gui.dialogs.word_preview import (
    build_content_preview_with_images,
    extract_images_from_article,
    show_batch_word_preview,
    show_word_preview,
)
from wechat_summarizer.presentation.gui.dialogs.word_preview_batch import (
    show_batch_word_preview as split_show_batch_word_preview,
)
from wechat_summarizer.presentation.gui.dialogs.word_preview_content import (
    build_content_preview_with_images as split_build_content_preview_with_images,
)
from wechat_summarizer.presentation.gui.dialogs.word_preview_content import (
    extract_images_from_article as split_extract_images_from_article,
)
from wechat_summarizer.presentation.gui.dialogs.word_preview_single import (
    show_word_preview as split_show_word_preview,
)
from wechat_summarizer.presentation.gui.frames import (
    BatchInputFrame,
    BatchResultsFrame,
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
    SingleArticleInputFrame,
    SingleArticleResultFrame,
)
from wechat_summarizer.presentation.gui.pages.batch_page import BatchPage
from wechat_summarizer.presentation.gui.pages.home_page import HomePage
from wechat_summarizer.presentation.gui.pages.settings_page import SettingsPage
from wechat_summarizer.presentation.gui.pages.single_page import SinglePage
from wechat_summarizer.presentation.gui.settings_api_actions import SettingsApiActionsMixin
from wechat_summarizer.presentation.gui.styles.colors import ModernColors
from wechat_summarizer.presentation.gui.utils import accessibility as accessibility_module
from wechat_summarizer.presentation.gui.utils import animation as animation_module
from wechat_summarizer.presentation.gui.utils import autosave as autosave_module
from wechat_summarizer.presentation.gui.utils import clipboard_detector as clipboard_module
from wechat_summarizer.presentation.gui.utils import lazy as lazy_module
from wechat_summarizer.presentation.gui.utils import microinteractions as microinteractions_module
from wechat_summarizer.presentation.gui.utils import performance as performance_module
from wechat_summarizer.presentation.gui.utils import shortcuts as shortcuts_module
from wechat_summarizer.presentation.gui.utils import theme_manager as theme_manager_module
from wechat_summarizer.presentation.gui.utils import transition as transition_module
from wechat_summarizer.presentation.gui.utils.accessibility import (
    AccessibilityHelper,
    FocusableElement,
    FocusDirection,
    FocusManager,
    FocusRingStyle,
    FocusRingStyleDict,
    KeyboardNavigable,
    LiveRegion,
    SkipLink,
)
from wechat_summarizer.presentation.gui.utils.accessibility_focus import (
    FocusManager as SplitFocusManager,
)
from wechat_summarizer.presentation.gui.utils.accessibility_helper import (
    AccessibilityHelper as SplitAccessibilityHelper,
)
from wechat_summarizer.presentation.gui.utils.accessibility_keyboard import (
    KeyboardNavigable as SplitKeyboardNavigable,
)
from wechat_summarizer.presentation.gui.utils.accessibility_live import (
    LiveRegion as SplitLiveRegion,
)
from wechat_summarizer.presentation.gui.utils.accessibility_models import (
    FocusableElement as SplitFocusableElement,
)
from wechat_summarizer.presentation.gui.utils.accessibility_models import (
    FocusDirection as SplitFocusDirection,
)
from wechat_summarizer.presentation.gui.utils.accessibility_models import (
    FocusRingStyle as SplitFocusRingStyle,
)
from wechat_summarizer.presentation.gui.utils.accessibility_models import (
    FocusRingStyleDict as SplitFocusRingStyleDict,
)
from wechat_summarizer.presentation.gui.utils.accessibility_skiplink import (
    SkipLink as SplitSkipLink,
)
from wechat_summarizer.presentation.gui.utils.animation import (
    AnimationEngine,
    Easing,
    EasingType,
    Tween,
    animate,
)
from wechat_summarizer.presentation.gui.utils.animation_easing import Easing as SplitEasing
from wechat_summarizer.presentation.gui.utils.animation_engine import (
    AnimationEngine as SplitAnimationEngine,
)
from wechat_summarizer.presentation.gui.utils.animation_facade import (
    animate as split_animate,
)
from wechat_summarizer.presentation.gui.utils.animation_models import (
    EasingType as SplitEasingType,
)
from wechat_summarizer.presentation.gui.utils.animation_models import Tween as SplitTween
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
from wechat_summarizer.presentation.gui.utils.clipboard_auto import (
    AutoLinkDetector as SplitAutoLinkDetector,
)
from wechat_summarizer.presentation.gui.utils.clipboard_browser import (
    BrowserDetector as SplitBrowserDetector,
)
from wechat_summarizer.presentation.gui.utils.clipboard_detector import (
    MAX_TEXT_LENGTH as CLIPBOARD_MAX_TEXT_LENGTH,
)
from wechat_summarizer.presentation.gui.utils.clipboard_detector import (
    MAX_URL_LENGTH as CLIPBOARD_MAX_URL_LENGTH,
)
from wechat_summarizer.presentation.gui.utils.clipboard_detector import (
    MAX_URLS as CLIPBOARD_MAX_URLS,
)
from wechat_summarizer.presentation.gui.utils.clipboard_detector import (
    AutoLinkDetector,
    BrowserDetector,
    ClipboardManager,
    DetectionResult,
    WeChatLinkDetector,
)
from wechat_summarizer.presentation.gui.utils.clipboard_manager import (
    ClipboardManager as SplitClipboardManager,
)
from wechat_summarizer.presentation.gui.utils.clipboard_models import (
    MAX_TEXT_LENGTH as SPLIT_CLIPBOARD_MAX_TEXT_LENGTH,
)
from wechat_summarizer.presentation.gui.utils.clipboard_models import (
    MAX_URL_LENGTH as SPLIT_CLIPBOARD_MAX_URL_LENGTH,
)
from wechat_summarizer.presentation.gui.utils.clipboard_models import (
    MAX_URLS as SPLIT_CLIPBOARD_MAX_URLS,
)
from wechat_summarizer.presentation.gui.utils.clipboard_models import (
    DetectionResult as SplitDetectionResult,
)
from wechat_summarizer.presentation.gui.utils.clipboard_wechat import (
    WeChatLinkDetector as SplitWeChatLinkDetector,
)
from wechat_summarizer.presentation.gui.utils.lazy import (
    ALLOWED_MODULE_PREFIX,
    LOAD_TIMEOUT_SECONDS,
    MAX_CACHED_COMPONENTS,
    MAX_CONCURRENT_LOADS,
    MAX_RETRY_COUNT,
    LazyComponent,
    LazyImage,
    LazyLoader,
    LazyWidget,
    LoadResult,
    LoadState,
    preload_components,
)
from wechat_summarizer.presentation.gui.utils.lazy import (
    lazy as lazy_decorator,
)
from wechat_summarizer.presentation.gui.utils.lazy_facade import lazy as split_lazy
from wechat_summarizer.presentation.gui.utils.lazy_facade import (
    preload_components as split_preload_components,
)
from wechat_summarizer.presentation.gui.utils.lazy_image import LazyImage as SplitLazyImage
from wechat_summarizer.presentation.gui.utils.lazy_loader import LazyLoader as SplitLazyLoader
from wechat_summarizer.presentation.gui.utils.lazy_models import (
    ALLOWED_MODULE_PREFIX as SPLIT_ALLOWED_MODULE_PREFIX,
)
from wechat_summarizer.presentation.gui.utils.lazy_models import (
    LOAD_TIMEOUT_SECONDS as SPLIT_LOAD_TIMEOUT_SECONDS,
)
from wechat_summarizer.presentation.gui.utils.lazy_models import (
    MAX_CACHED_COMPONENTS as SPLIT_MAX_CACHED_COMPONENTS,
)
from wechat_summarizer.presentation.gui.utils.lazy_models import (
    MAX_CONCURRENT_LOADS as SPLIT_MAX_CONCURRENT_LOADS,
)
from wechat_summarizer.presentation.gui.utils.lazy_models import (
    MAX_RETRY_COUNT as SPLIT_MAX_RETRY_COUNT,
)
from wechat_summarizer.presentation.gui.utils.lazy_models import (
    LazyComponent as SplitLazyComponent,
)
from wechat_summarizer.presentation.gui.utils.lazy_models import LoadResult as SplitLoadResult
from wechat_summarizer.presentation.gui.utils.lazy_models import LoadState as SplitLoadState
from wechat_summarizer.presentation.gui.utils.lazy_widget import LazyWidget as SplitLazyWidget
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
from wechat_summarizer.presentation.gui.utils.performance import (
    CRITICAL_MEMORY_MB,
    MAX_HISTORY_SIZE,
    MAX_SLOW_OPS_LOG,
    MONITOR_INTERVAL_MS,
    SLOW_OP_THRESHOLD_MS,
    WARNING_MEMORY_MB,
    PerformanceLevel,
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceOverlay,
    PerformanceTimer,
    SlowOperation,
    get_monitor,
    show_overlay,
    start_monitoring,
    stop_monitoring,
    timer,
)
from wechat_summarizer.presentation.gui.utils.performance_constants import (
    CRITICAL_MEMORY_MB as SPLIT_CRITICAL_MEMORY_MB,
)
from wechat_summarizer.presentation.gui.utils.performance_constants import (
    MAX_HISTORY_SIZE as SPLIT_MAX_HISTORY_SIZE,
)
from wechat_summarizer.presentation.gui.utils.performance_constants import (
    MAX_SLOW_OPS_LOG as SPLIT_MAX_SLOW_OPS_LOG,
)
from wechat_summarizer.presentation.gui.utils.performance_constants import (
    MONITOR_INTERVAL_MS as SPLIT_MONITOR_INTERVAL_MS,
)
from wechat_summarizer.presentation.gui.utils.performance_constants import (
    SLOW_OP_THRESHOLD_MS as SPLIT_SLOW_OP_THRESHOLD_MS,
)
from wechat_summarizer.presentation.gui.utils.performance_constants import (
    WARNING_MEMORY_MB as SPLIT_WARNING_MEMORY_MB,
)
from wechat_summarizer.presentation.gui.utils.performance_facade import (
    get_monitor as split_get_monitor,
)
from wechat_summarizer.presentation.gui.utils.performance_facade import (
    show_overlay as split_show_overlay,
)
from wechat_summarizer.presentation.gui.utils.performance_facade import (
    start_monitoring as split_start_monitoring,
)
from wechat_summarizer.presentation.gui.utils.performance_facade import (
    stop_monitoring as split_stop_monitoring,
)
from wechat_summarizer.presentation.gui.utils.performance_facade import timer as split_timer
from wechat_summarizer.presentation.gui.utils.performance_models import (
    PerformanceLevel as SplitPerformanceLevel,
)
from wechat_summarizer.presentation.gui.utils.performance_models import (
    PerformanceMetrics as SplitPerformanceMetrics,
)
from wechat_summarizer.presentation.gui.utils.performance_models import (
    SlowOperation as SplitSlowOperation,
)
from wechat_summarizer.presentation.gui.utils.performance_monitor import (
    PerformanceMonitor as SplitPerformanceMonitor,
)
from wechat_summarizer.presentation.gui.utils.performance_overlay import (
    PerformanceOverlay as SplitPerformanceOverlay,
)
from wechat_summarizer.presentation.gui.utils.performance_timer import (
    PerformanceTimer as SplitPerformanceTimer,
)
from wechat_summarizer.presentation.gui.utils.shortcuts import (
    KeyboardShortcutManager,
    Shortcut,
    ShortcutHelpPanel,
)
from wechat_summarizer.presentation.gui.utils.shortcuts_manager import (
    KeyboardShortcutManager as SplitKeyboardShortcutManager,
)
from wechat_summarizer.presentation.gui.utils.shortcuts_models import Shortcut as SplitShortcut
from wechat_summarizer.presentation.gui.utils.shortcuts_models import default_shortcuts
from wechat_summarizer.presentation.gui.utils.shortcuts_panel import (
    ShortcutHelpPanel as SplitShortcutHelpPanel,
)
from wechat_summarizer.presentation.gui.utils.theme_manager import (
    AccessibilitySettings,
    AppearanceMode,
    ContrastMode,
    ThemeManager,
    theme_manager,
)
from wechat_summarizer.presentation.gui.utils.theme_models import (
    AccessibilitySettings as SplitThemeAccessibilitySettings,
)
from wechat_summarizer.presentation.gui.utils.theme_models import (
    AppearanceMode as SplitAppearanceMode,
)
from wechat_summarizer.presentation.gui.utils.theme_models import (
    ContrastMode as SplitContrastMode,
)
from wechat_summarizer.presentation.gui.utils.theme_palettes import (
    BASE_FONT_SIZES as SPLIT_THEME_BASE_FONT_SIZES,
)
from wechat_summarizer.presentation.gui.utils.theme_palettes import (
    HIGH_CONTRAST_THEMES as SPLIT_HIGH_CONTRAST_THEMES,
)
from wechat_summarizer.presentation.gui.utils.theme_palettes import THEMES as SPLIT_THEMES
from wechat_summarizer.presentation.gui.utils.theme_storage import (
    load_accessibility_settings,
    save_accessibility_settings,
)
from wechat_summarizer.presentation.gui.utils.transition import (
    EasingFunction,
    PageRouter,
    PageTransition,
    TransitionConfig,
    TransitionType,
)
from wechat_summarizer.presentation.gui.utils.transition_easing import (
    Easing as SplitTransitionEasing,
)
from wechat_summarizer.presentation.gui.utils.transition_models import (
    EasingFunction as SplitTransitionEasingFunction,
)
from wechat_summarizer.presentation.gui.utils.transition_models import (
    TransitionConfig as SplitTransitionConfig,
)
from wechat_summarizer.presentation.gui.utils.transition_models import (
    TransitionType as SplitTransitionType,
)
from wechat_summarizer.presentation.gui.utils.transition_page import (
    PageTransition as SplitPageTransition,
)
from wechat_summarizer.presentation.gui.utils.transition_router import PageRouter as SplitPageRouter


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
def test_icon_module_keeps_compatibility_exports() -> None:
    assert icons_module.IconManager is SplitIconManager
    assert icons_module.IconSize is SplitIconSize
    assert icons_module.IconStyle is SplitIconStyle
    assert icons_module.SVGPathParser is SplitSVGPathParser
    assert icons_module.ICON_PATHS is SPLIT_ICON_PATHS
    assert icons_module.get_icon is split_get_icon
    assert icons_module.get_icon_tk is split_get_icon_tk
    assert icons_module.list_icons is split_list_icons
    assert IconManager is SplitIconManager
    assert IconSize is SplitIconSize
    assert IconStyle is SplitIconStyle
    assert SVGPathParser is SplitSVGPathParser
    assert ICON_PATHS is SPLIT_ICON_PATHS
    assert get_icon is split_get_icon
    assert get_icon_tk is split_get_icon_tk
    assert list_icons is split_list_icons


@pytest.mark.unit
def test_icon_library_preserves_models_paths_and_parser_behavior() -> None:
    available_icons = set(list_icons())
    parsed_commands = SVGPathParser.parse("M0 0 L10 10 Z")

    assert IconSize.MEDIUM.value == 24
    assert IconStyle.OUTLINED.value == "outlined"
    assert {"save", "settings", "today"}.issubset(available_icons)
    assert [command for command, _points in parsed_commands] == ["move", "line", "close"]
    assert IconManager._validate_color("#fff") is True
    assert IconManager._validate_color("#123abc") is True
    assert IconManager._validate_color("rgb(255, 255, 255)") is False
    assert IconManager._parse_color("#fff") == (255, 255, 255, 255)


@pytest.mark.unit
def test_icon_asset_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_paths.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_runtime.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_parser.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_renderer.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/assets/icons_facade.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


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
def test_single_page_delegates_article_sections_to_frames() -> None:
    assert "_build" in SingleArticleInputFrame.__dict__
    assert "_build" in SingleArticleResultFrame.__dict__
    assert "_build_textbox_section" in SingleArticleResultFrame.__dict__
    assert "on_page_shown" in SinglePage.__dict__
    assert "_show_clipboard_banner" in SinglePage.__dict__
    assert "_copy_textbox" in SinglePage.__dict__


@pytest.mark.unit
def test_single_page_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/pages/single_page.py",
        repo_root / "src/wechat_summarizer/presentation/gui/frames/single_article.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_batch_page_delegates_processing_sections_to_frames() -> None:
    assert "_build" in BatchInputFrame.__dict__
    assert "_build_url_actions" in BatchInputFrame.__dict__
    assert "_build_options" in BatchInputFrame.__dict__
    assert "_build_processing_actions" in BatchInputFrame.__dict__
    assert "_build" in BatchResultsFrame.__dict__
    assert "_build_progress_detail" in BatchResultsFrame.__dict__
    assert "_build_export_buttons" in BatchResultsFrame.__dict__
    assert "set_processing_state" in BatchPage.__dict__
    assert "_build_progress_detail" not in BatchPage.__dict__
    assert "_build_export_buttons" not in BatchPage.__dict__


@pytest.mark.unit
def test_batch_page_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/pages/batch_page.py",
        repo_root / "src/wechat_summarizer/presentation/gui/frames/batch_processing.py",
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
def test_card_module_keeps_compatibility_exports() -> None:
    assert card_module._CTK_AVAILABLE is SPLIT_CARD_CTK_AVAILABLE
    assert card_module.ctk is split_card_ctk
    assert card_module.ModernCard is SplitModernCard
    assert card_module.ContentCard is SplitContentCard
    assert card_module.ActionCard is SplitActionCard
    assert card_module.StatCard is SplitStatCard
    assert card_module.CardStyle is SplitCardStyle
    assert card_module.CornerRadius is SplitCornerRadius
    assert card_module.ShadowDepth is SplitShadowDepth
    assert card_module.create_card is split_create_card
    assert card_module.create_content_card is split_create_content_card
    assert CARD_CTK_AVAILABLE is SPLIT_CARD_CTK_AVAILABLE
    assert card_ctk is split_card_ctk
    assert ModernCard is SplitModernCard
    assert ContentCard is SplitContentCard
    assert ActionCard is SplitActionCard
    assert StatCard is SplitStatCard
    assert CardStyle is SplitCardStyle
    assert CornerRadius is SplitCornerRadius
    assert ShadowDepth is SplitShadowDepth
    assert create_card is split_create_card
    assert create_content_card is split_create_content_card


@pytest.mark.unit
def test_card_models_preserve_values() -> None:
    assert ShadowDepth.NONE.value == 0
    assert ShadowDepth.SHALLOW.value == 1
    assert ShadowDepth.MEDIUM.value == 2
    assert ShadowDepth.DEEP.value == 3
    assert ShadowDepth.ELEVATED.value == 4
    assert CornerRadius.SMALL.value == 8
    assert CornerRadius.MEDIUM.value == 16
    assert CornerRadius.LARGE.value == 24
    assert CornerRadius.XLARGE.value == 32
    assert CardStyle.SOLID.value == "solid"
    assert CardStyle.OUTLINED.value == "outlined"
    assert CardStyle.ELEVATED.value == "elevated"
    assert CardStyle.GLASS.value == "glass"


@pytest.mark.unit
def test_card_factory_preserves_return_types(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: dict[str, object] = {}

    class DummyModernCard:
        def __init__(self, master, **kwargs):  # type: ignore[no-untyped-def]
            calls["modern"] = {"master": master, **kwargs}

    class DummyContentCard:
        def __init__(self, master, **kwargs):  # type: ignore[no-untyped-def]
            calls["content"] = {"master": master, **kwargs}

    monkeypatch.setattr(
        "wechat_summarizer.presentation.gui.components.card_factory.ModernCard",
        DummyModernCard,
    )
    monkeypatch.setattr(
        "wechat_summarizer.presentation.gui.components.card_factory.ContentCard",
        DummyContentCard,
    )

    master = object()
    modern = create_card(master, width=123, height=45, theme="light", style=CardStyle.GLASS)
    content = create_content_card(master, title="标题", subtitle="副标题", theme="dark", width=456)

    assert isinstance(modern, DummyModernCard)
    assert isinstance(content, DummyContentCard)
    assert calls["modern"] == {
        "master": master,
        "width": 123,
        "height": 45,
        "theme": "light",
        "style": CardStyle.GLASS,
    }
    assert calls["content"] == {
        "master": master,
        "title": "标题",
        "subtitle": "副标题",
        "theme": "dark",
        "width": 456,
    }


@pytest.mark.unit
def test_card_base_preserves_color_and_state_logic() -> None:
    card = ModernCard.__new__(ModernCard)

    assert card._get_dark_bg_color(CardStyle.GLASS) == ModernColors.DARK_GLASS_SOLID
    assert card._get_dark_bg_color(CardStyle.OUTLINED) == "transparent"
    assert card._get_dark_bg_color(CardStyle.ELEVATED) == ModernColors.DARK_CARD
    assert card._get_light_bg_color(CardStyle.GLASS) == ModernColors.LIGHT_GLASS_SOLID
    assert card._get_light_bg_color(CardStyle.OUTLINED) == "transparent"
    assert card._get_light_bg_color(CardStyle.ELEVATED) == ModernColors.LIGHT_CARD

    card.set_shadow_depth(ShadowDepth.DEEP)

    assert card._shadow_depth is ShadowDepth.DEEP


@pytest.mark.unit
def test_card_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/card.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_base.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_content.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_action.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_stat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/card_factory.py",
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
def test_virtuallist_module_keeps_compatibility_exports_and_composition() -> None:
    item = VirtualItem(index=2, data={"title": "demo"}, height=48, y_offset=96)

    assert virtuallist_module.VirtualItem is SplitVirtualItem
    assert VirtualItem is SplitVirtualItem
    assert VirtualListRenderMixin in VirtualList.__mro__
    assert VIRTUAL_LIST_MAX_ITEMS == SPLIT_VIRTUAL_LIST_MAX_ITEMS == 100000
    assert VIRTUAL_LIST_MAX_ITEM_HEIGHT == SPLIT_VIRTUAL_LIST_MAX_ITEM_HEIGHT == 500
    assert VIRTUAL_LIST_MIN_ITEM_HEIGHT == SPLIT_VIRTUAL_LIST_MIN_ITEM_HEIGHT == 20
    assert VIRTUAL_LIST_RENDER_TIMEOUT_MS == SPLIT_VIRTUAL_LIST_RENDER_TIMEOUT_MS == 100
    assert VIRTUAL_LIST_SCROLL_THROTTLE_MS == SPLIT_VIRTUAL_LIST_SCROLL_THROTTLE_MS == 16
    assert item.index == 2
    assert item.data == {"title": "demo"}
    assert item.height == 48
    assert item.y_offset == 96


@pytest.mark.unit
def test_virtuallist_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/virtuallist.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/virtuallist_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/virtuallist_render.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/virtuallist_demo.py",
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
def test_select_module_keeps_compatibility_exports_and_composition() -> None:
    option = SelectOption(value="markdown", label="Markdown", disabled=True)

    assert select_module.ModernSelect is SplitModernSelect
    assert select_module.SelectMode is SplitSelectMode
    assert select_module.SelectOption is SplitSelectOption
    assert select_module.create_select is split_create_select
    assert ModernSelect is SplitModernSelect
    assert SelectMode is SplitSelectMode
    assert SelectOption is SplitSelectOption
    assert create_select is split_create_select
    assert SelectDropdownMixin in ModernSelect.__mro__
    assert SelectMode.SINGLE.value == "single"
    assert SelectMode.MULTIPLE.value == "multiple"
    assert option.value == "markdown"
    assert option.label == "Markdown"
    assert option.disabled is True
    assert ModernSelect.MAX_VISIBLE_OPTIONS == 8
    assert ModernSelect.MAX_OPTIONS == 10000


@pytest.mark.unit
def test_select_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/select.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/select_compat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/select_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/select_dropdown.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/select_modern.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/select_factory.py",
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
def test_sidebar_module_keeps_compatibility_exports_and_composition() -> None:
    child = NavItem(id="recent", label="最近", icon="R", badge=10000)
    item = NavItem(id="home", label="首页", icon="H", badge=-4, children=[child])

    assert sidebar_module.CollapsibleSidebar is SplitCollapsibleSidebar
    assert sidebar_module.NavItem is SplitNavItem
    assert sidebar_module.Tooltip is SplitTooltip
    assert sidebar_module.default_sidebar_state_file is split_default_sidebar_state_file
    assert sidebar_module.resolve_sidebar_state_file is split_resolve_sidebar_state_file
    assert CollapsibleSidebar is SplitCollapsibleSidebar
    assert NavItem is SplitNavItem
    assert Tooltip is SplitTooltip
    assert default_sidebar_state_file is split_default_sidebar_state_file
    assert resolve_sidebar_state_file is split_resolve_sidebar_state_file
    assert SidebarAnimationMixin in CollapsibleSidebar.__mro__
    assert SidebarItemsMixin in CollapsibleSidebar.__mro__
    assert SidebarStateMixin in CollapsibleSidebar.__mro__
    assert item.children == [child]
    assert clamp_badge(item.badge) == 0
    assert clamp_badge(child.badge) == CollapsibleSidebar.MAX_BADGE
    assert CollapsibleSidebar.EXPANDED_WIDTH == 240
    assert CollapsibleSidebar.COLLAPSED_WIDTH == 60


@pytest.mark.unit
def test_sidebar_state_path_validation_uses_safe_default(tmp_path: Path) -> None:
    default_path = default_sidebar_state_file()
    repo_root = Path(__file__).resolve().parents[1]
    user_state_file = Path.home() / ".wechat_summarizer" / "sidebar-user-owned.json"
    local_state_file = (
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_state.json"
    )
    unsafe_state_file = Path("/tmp/sidebar_state.json")

    assert resolve_sidebar_state_file(None) == default_path
    assert resolve_sidebar_state_file(str(unsafe_state_file)) == default_path
    assert resolve_sidebar_state_file(str(local_state_file)) == str(local_state_file)
    assert resolve_sidebar_state_file(str(user_state_file)) == str(user_state_file)


@pytest.mark.unit
def test_sidebar_component_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_tooltip.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_state.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_items.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_animation.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_core.py",
        repo_root / "src/wechat_summarizer/presentation/gui/components/sidebar_demo.py",
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
def test_animation_module_keeps_compatibility_exports() -> None:
    assert animation_module.AnimationEngine is SplitAnimationEngine
    assert animation_module.Easing is SplitEasing
    assert animation_module.EasingType is SplitEasingType
    assert animation_module.Tween is SplitTween
    assert animation_module.animate is split_animate
    assert AnimationEngine is SplitAnimationEngine
    assert Easing is SplitEasing
    assert EasingType is SplitEasingType
    assert Tween is SplitTween
    assert animate is split_animate
    assert EasingType.EASE_OUT_CUBIC.value == "ease_out_cubic"
    assert Easing.get(EasingType.LINEAR)(0.4) == 0.4
    assert AnimationEngine.MAX_ANIMATIONS == 50
    assert AnimationEngine.MAX_DURATION == 10000


@pytest.mark.unit
def test_animation_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/animation.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/animation_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/animation_easing.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/animation_engine.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/animation_facade.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/animation_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_accessibility_module_keeps_compatibility_exports() -> None:
    assert accessibility_module.AccessibilityHelper is SplitAccessibilityHelper
    assert accessibility_module.FocusDirection is SplitFocusDirection
    assert accessibility_module.FocusManager is SplitFocusManager
    assert accessibility_module.FocusRingStyle is SplitFocusRingStyle
    assert accessibility_module.FocusRingStyleDict is SplitFocusRingStyleDict
    assert accessibility_module.FocusableElement is SplitFocusableElement
    assert accessibility_module.KeyboardNavigable is SplitKeyboardNavigable
    assert accessibility_module.LiveRegion is SplitLiveRegion
    assert accessibility_module.SkipLink is SplitSkipLink
    assert AccessibilityHelper is SplitAccessibilityHelper
    assert FocusDirection is SplitFocusDirection
    assert FocusManager is SplitFocusManager
    assert FocusRingStyle is SplitFocusRingStyle
    assert FocusRingStyleDict is SplitFocusRingStyleDict
    assert FocusableElement is SplitFocusableElement
    assert KeyboardNavigable is SplitKeyboardNavigable
    assert LiveRegion is SplitLiveRegion
    assert SkipLink is SplitSkipLink


@pytest.mark.unit
def test_accessibility_models_preserve_wcag_focused_defaults() -> None:
    assert FocusDirection.NEXT.value == "next"
    assert FocusDirection.PREVIOUS.value == "previous"
    assert FocusRingStyle.DEFAULT["color"] == "#3b82f6"
    assert FocusRingStyle.DEFAULT["width"] == 2
    assert FocusRingStyle.HIGH_CONTRAST["width"] == 3
    assert FocusRingStyle.DASHED["style"] == "dashed"
    assert FocusableElement(widget=None, tab_index=2, label="Save").label == "Save"


@pytest.mark.unit
def test_accessibility_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_focus.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_skiplink.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_keyboard.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_live.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_helper.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/accessibility_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_word_preview_module_keeps_compatibility_exports() -> None:
    assert word_preview_module.build_content_preview_with_images is (
        split_build_content_preview_with_images
    )
    assert word_preview_module.extract_images_from_article is split_extract_images_from_article
    assert word_preview_module.show_batch_word_preview is split_show_batch_word_preview
    assert word_preview_module.show_word_preview is split_show_word_preview
    assert build_content_preview_with_images is split_build_content_preview_with_images
    assert extract_images_from_article is split_extract_images_from_article
    assert show_batch_word_preview is split_show_batch_word_preview
    assert show_word_preview is split_show_word_preview


@pytest.mark.unit
def test_word_preview_content_preview_preserves_images_and_structures() -> None:
    html = """
    <div id="js_content">
      <h2>章节标题</h2>
      <p>第一段<img data-src="https://example.com/photo.png" /></p>
      <ul><li>要点一</li><li>要点二</li></ul>
      <blockquote>引用内容</blockquote>
      <table><tr><th>列名</th></tr><tr><td>很长很长很长很长很长很长很长的单元格</td></tr></table>
      <img src="https://example.com/emoji.png" />
    </div>
    """
    article = Article(
        url=ArticleURL.from_string("https://mp.weixin.qq.com/s/test-preview"),
        title="预览测试",
        content=ArticleContent.from_html(html),
    )

    preview = build_content_preview_with_images(article)
    images = extract_images_from_article(article)

    assert "【章节标题】" in preview
    assert "[图片 1]" in preview
    assert "  • 要点一" in preview
    assert "「引用内容」" in preview
    assert "┌────────── 表格 ──────────┐" in preview
    assert images == ["https://example.com/photo.png", "https://example.com/emoji.png"]


@pytest.mark.unit
def test_word_preview_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/word_preview.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/word_preview_batch.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/word_preview_content.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/word_preview_render.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/word_preview_single.py",
        repo_root / "src/wechat_summarizer/presentation/gui/dialogs/word_preview_window.py",
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


@pytest.mark.unit
def test_clipboard_detector_module_keeps_compatibility_exports() -> None:
    result = DetectionResult(
        links=["https://mp.weixin.qq.com/s/example123"], source="text", message="ok"
    )

    assert clipboard_module.AutoLinkDetector is SplitAutoLinkDetector
    assert clipboard_module.BrowserDetector is SplitBrowserDetector
    assert clipboard_module.ClipboardManager is SplitClipboardManager
    assert clipboard_module.DetectionResult is SplitDetectionResult
    assert clipboard_module.WeChatLinkDetector is SplitWeChatLinkDetector
    assert AutoLinkDetector is SplitAutoLinkDetector
    assert BrowserDetector is SplitBrowserDetector
    assert ClipboardManager is SplitClipboardManager
    assert DetectionResult is SplitDetectionResult
    assert WeChatLinkDetector is SplitWeChatLinkDetector
    assert CLIPBOARD_MAX_TEXT_LENGTH == SPLIT_CLIPBOARD_MAX_TEXT_LENGTH
    assert CLIPBOARD_MAX_URL_LENGTH == SPLIT_CLIPBOARD_MAX_URL_LENGTH
    assert CLIPBOARD_MAX_URLS == SPLIT_CLIPBOARD_MAX_URLS
    assert result.links == ["https://mp.weixin.qq.com/s/example123"]
    assert result.source == "text"
    assert WeChatLinkDetector.is_valid_wechat_link("https://mp.weixin.qq.com/s/example123")
    assert not WeChatLinkDetector.is_valid_wechat_link("https://example.com/s/example123")


@pytest.mark.unit
def test_clipboard_detector_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/clipboard_detector.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/clipboard_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/clipboard_wechat.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/clipboard_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/clipboard_browser.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/clipboard_auto.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_lazy_module_keeps_compatibility_exports() -> None:
    assert lazy_module.LazyLoader is SplitLazyLoader
    assert lazy_module.LazyWidget is SplitLazyWidget
    assert lazy_module.LazyImage is SplitLazyImage
    assert lazy_module.LazyComponent is SplitLazyComponent
    assert lazy_module.LoadResult is SplitLoadResult
    assert lazy_module.LoadState is SplitLoadState
    assert lazy_module.lazy is split_lazy
    assert lazy_module.preload_components is split_preload_components
    assert LazyLoader is SplitLazyLoader
    assert LazyWidget is SplitLazyWidget
    assert LazyImage is SplitLazyImage
    assert LazyComponent is SplitLazyComponent
    assert LoadResult is SplitLoadResult
    assert LoadState is SplitLoadState
    assert lazy_decorator is split_lazy
    assert preload_components is split_preload_components
    assert MAX_CONCURRENT_LOADS == SPLIT_MAX_CONCURRENT_LOADS
    assert MAX_CACHED_COMPONENTS == SPLIT_MAX_CACHED_COMPONENTS
    assert MAX_RETRY_COUNT == SPLIT_MAX_RETRY_COUNT
    assert LOAD_TIMEOUT_SECONDS == SPLIT_LOAD_TIMEOUT_SECONDS
    assert ALLOWED_MODULE_PREFIX == SPLIT_ALLOWED_MODULE_PREFIX
    assert LoadState.IDLE.value == "idle"
    assert LoadResult(state=LoadState.SUCCESS, component=str).component is str


@pytest.mark.unit
def test_lazy_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy_loader.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy_widget.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy_image.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy_facade.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/lazy_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_shortcuts_module_keeps_compatibility_exports() -> None:
    shortcut = Shortcut(id="save", name="保存", keys="Ctrl+S", group="文件")

    assert shortcuts_module.KeyboardShortcutManager is SplitKeyboardShortcutManager
    assert shortcuts_module.Shortcut is SplitShortcut
    assert shortcuts_module.ShortcutHelpPanel is SplitShortcutHelpPanel
    assert KeyboardShortcutManager is SplitKeyboardShortcutManager
    assert Shortcut is SplitShortcut
    assert ShortcutHelpPanel is SplitShortcutHelpPanel
    assert KeyboardShortcutManager.MAX_SHORTCUTS == 100
    assert KeyboardShortcutManager.MODIFIER_MAP["Ctrl"] == "Control"
    assert shortcut.keys == "Ctrl+S"
    assert shortcut.enabled is True
    assert any(item.id == "select_all" for item in default_shortcuts())


@pytest.mark.unit
def test_shortcuts_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/shortcuts.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/shortcuts_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/shortcuts_storage.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/shortcuts_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/shortcuts_panel.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/shortcuts_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_theme_manager_module_keeps_compatibility_exports(tmp_path: Path) -> None:
    settings_path = tmp_path / "accessibility.json"
    settings = AccessibilitySettings(
        font_scale=3.0,
        contrast_mode="high",
        reduce_motion=True,
        reduce_transparency=True,
    )

    save_accessibility_settings(str(settings_path), settings)
    loaded = load_accessibility_settings(str(settings_path))

    assert theme_manager_module.AccessibilitySettings is SplitThemeAccessibilitySettings
    assert theme_manager_module.AppearanceMode is SplitAppearanceMode
    assert theme_manager_module.ContrastMode is SplitContrastMode
    assert AccessibilitySettings is SplitThemeAccessibilitySettings
    assert AppearanceMode is SplitAppearanceMode
    assert ContrastMode is SplitContrastMode
    assert isinstance(theme_manager, ThemeManager)
    assert ThemeManager.THEMES is SPLIT_THEMES
    assert ThemeManager.HIGH_CONTRAST_THEMES is SPLIT_HIGH_CONTRAST_THEMES
    assert ThemeManager.BASE_FONT_SIZES is SPLIT_THEME_BASE_FONT_SIZES
    assert loaded.font_scale == AccessibilitySettings.MAX_FONT_SCALE
    assert loaded.contrast_mode == "high"
    assert loaded.reduce_motion is True
    assert loaded.reduce_transparency is True


@pytest.mark.unit
def test_theme_manager_preserves_accessibility_and_palette_behavior(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manager = object.__new__(ThemeManager)
    manager._initialized = True
    manager._current_mode = AppearanceMode.LIGHT
    manager._callbacks = []
    manager._accessibility_callbacks = []
    manager._config_file = str(tmp_path / "accessibility.json")
    manager._accessibility = AccessibilitySettings()

    saved: list[float] = []
    manager.on_accessibility_changed(lambda settings: saved.append(settings.font_scale))

    manager.set_font_scale(1.5)
    assert manager.get_scaled_font_size("base") == 21
    assert saved == [1.5]

    manager.set_contrast_mode(ContrastMode.HIGH)
    assert manager.is_high_contrast() is True
    assert manager.get_colors(AppearanceMode.LIGHT)["text"] == "#000000"

    monkeypatch.setattr(
        "wechat_summarizer.presentation.gui.utils.theme_manager.should_reduce_motion_for_system",
        lambda: True,
    )
    assert manager.should_reduce_motion() is True


@pytest.mark.unit
def test_theme_manager_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/theme_manager.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/theme_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/theme_palettes.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/theme_platform.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/theme_storage.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_transition_module_keeps_compatibility_exports() -> None:
    assert transition_module.Easing is SplitTransitionEasing
    assert transition_module.EasingFunction is SplitTransitionEasingFunction
    assert transition_module.TransitionConfig is SplitTransitionConfig
    assert transition_module.TransitionType is SplitTransitionType
    assert transition_module.PageTransition is SplitPageTransition
    assert transition_module.PageRouter is SplitPageRouter
    assert EasingFunction is SplitTransitionEasingFunction
    assert TransitionConfig is SplitTransitionConfig
    assert TransitionType is SplitTransitionType
    assert PageTransition is SplitPageTransition
    assert PageRouter is SplitPageRouter


@pytest.mark.unit
def test_transition_models_and_easing_preserve_values() -> None:
    config = TransitionConfig()

    assert TransitionType.FADE.value == "fade"
    assert TransitionType.SLIDE_LEFT.value == "slide_left"
    assert TransitionType.SCALE_FADE.value == "scale_fade"
    assert TransitionType.NONE.value == "none"
    assert EasingFunction.EASE_OUT_CUBIC.value == "ease_out_cubic"
    assert config.type is TransitionType.FADE
    assert config.duration == 300
    assert config.easing is EasingFunction.EASE_OUT_CUBIC
    assert config.delay == 0
    assert SplitTransitionEasing.linear(0.25) == 0.25
    assert SplitTransitionEasing.ease_in(0.5) == 0.25
    assert SplitTransitionEasing.ease_out(0.5) == 0.75
    assert SplitTransitionEasing.get(EasingFunction.LINEAR)(0.4) == 0.4


@pytest.mark.unit
def test_page_transition_preserves_limits_and_instant_switch() -> None:
    class FakeContainer:
        def winfo_width(self) -> int:
            return 300

        def winfo_height(self) -> int:
            return 200

        def after(self, _delay: int, callback):  # type: ignore[no-untyped-def]
            callback()
            return "after-id"

        def after_cancel(self, _animation_id: str) -> None:
            self.cancelled = _animation_id

    class FakePage:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, object]]] = []

        def place(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
            self.calls.append(("place", kwargs))

        def place_forget(self) -> None:
            self.calls.append(("place_forget", {}))

        def lift(self) -> None:
            self.calls.append(("lift", {}))

        def lower(self) -> None:
            self.calls.append(("lower", {}))

    transition = PageTransition(
        FakeContainer(),
        TransitionConfig(duration=5000, delay=5000, easing=EasingFunction.LINEAR),
    )
    page = FakePage()
    completed: list[str] = []

    transition.transition_to(page, lambda: completed.append("done"), TransitionType.NONE)

    assert transition.config.duration == PageTransition.MAX_DURATION
    assert transition.config.delay == 1000
    assert transition.get_current_page() is page
    assert transition.is_animating() is False
    assert completed == ["done"]
    assert page.calls == [("place", {"x": 0, "y": 0, "relwidth": 1.0, "relheight": 1.0})]


@pytest.mark.unit
def test_page_router_preserves_history_and_reverse_transition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transitions: list[tuple[object, TransitionType | None]] = []

    class FakeTransition:
        def __init__(self, _container, _config):  # type: ignore[no-untyped-def]
            pass

        def transition_to(self, page, on_complete, transition_type=None):  # type: ignore[no-untyped-def]
            transitions.append((page, transition_type))
            on_complete()

    monkeypatch.setattr(
        "wechat_summarizer.presentation.gui.utils.transition_router.PageTransition",
        FakeTransition,
    )
    router = PageRouter(object(), TransitionConfig(type=TransitionType.SLIDE_LEFT))
    events: list[tuple[str, str]] = []
    page_a = object()
    page_b = object()

    router.register_page("a", page_a)
    router.register_page("b", page_b)
    router.on_route_change(lambda old, new: events.append((old, new)))

    router.navigate_to("a", TransitionType.NONE)
    router.navigate_to("b")
    went_back = router.go_back()

    assert went_back is True
    assert router.get_current_route() == "a"
    assert router.get_history() == ["b"]
    assert transitions == [
        (page_a, TransitionType.NONE),
        (page_b, None),
        (page_a, TransitionType.SLIDE_RIGHT),
    ]
    assert events == [("a", "b"), ("b", "a")]


@pytest.mark.unit
def test_transition_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/transition.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/transition_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/transition_easing.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/transition_page.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/transition_router.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/transition_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target


@pytest.mark.unit
def test_performance_module_keeps_compatibility_exports() -> None:
    assert performance_module.PerformanceLevel is SplitPerformanceLevel
    assert performance_module.PerformanceMetrics is SplitPerformanceMetrics
    assert performance_module.SlowOperation is SplitSlowOperation
    assert performance_module.PerformanceMonitor is SplitPerformanceMonitor
    assert performance_module.PerformanceOverlay is SplitPerformanceOverlay
    assert performance_module.PerformanceTimer is SplitPerformanceTimer
    assert performance_module.get_monitor is split_get_monitor
    assert performance_module.start_monitoring is split_start_monitoring
    assert performance_module.stop_monitoring is split_stop_monitoring
    assert performance_module.timer is split_timer
    assert performance_module.show_overlay is split_show_overlay
    assert PerformanceLevel is SplitPerformanceLevel
    assert PerformanceMetrics is SplitPerformanceMetrics
    assert SlowOperation is SplitSlowOperation
    assert PerformanceMonitor is SplitPerformanceMonitor
    assert PerformanceOverlay is SplitPerformanceOverlay
    assert PerformanceTimer is SplitPerformanceTimer
    assert get_monitor is split_get_monitor
    assert start_monitoring is split_start_monitoring
    assert stop_monitoring is split_stop_monitoring
    assert timer is split_timer
    assert show_overlay is split_show_overlay
    assert split_get_monitor() is SplitPerformanceMonitor()
    assert SPLIT_MAX_HISTORY_SIZE == MAX_HISTORY_SIZE
    assert SPLIT_MAX_SLOW_OPS_LOG == MAX_SLOW_OPS_LOG
    assert SPLIT_SLOW_OP_THRESHOLD_MS == SLOW_OP_THRESHOLD_MS
    assert SPLIT_WARNING_MEMORY_MB == WARNING_MEMORY_MB
    assert SPLIT_CRITICAL_MEMORY_MB == CRITICAL_MEMORY_MB
    assert SPLIT_MONITOR_INTERVAL_MS == MONITOR_INTERVAL_MS


@pytest.mark.unit
def test_performance_files_stay_below_gui_file_target() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_constants.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_models.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_timer.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_monitor.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_overlay.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_facade.py",
        repo_root / "src/wechat_summarizer/presentation/gui/utils/performance_demo.py",
    ]

    for target in targets:
        assert len(target.read_text(encoding="utf-8").splitlines()) < 400, target
