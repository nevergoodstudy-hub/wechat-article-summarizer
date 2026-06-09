"""Reusable GUI frame sections."""

from .batch_export import BatchExportActionsFrame
from .batch_processing import BatchInputFrame, BatchResultsFrame
from .history import HistoryHeaderFrame, HistoryItemFrame, HistoryListFrame
from .home_dashboard import (
    HomeActionCardsFrame,
    HomeTipBarFrame,
    HomeWelcomeFrame,
)
from .home_info import HomeInfoRowFrame, HomeRecentRecordsFrame, HomeStatusOverviewFrame
from .settings_preferences import (
    SettingsExportSection,
    SettingsLanguageSection,
    SettingsPerformanceSection,
    SettingsQuickActionsFrame,
    SettingsSystemSection,
)
from .settings_service import SettingsApiKeysSection, SettingsSummarizerSection
from .single_article import SingleArticleInputFrame, SingleArticleResultFrame
from .single_clipboard import SingleClipboardBannerFrame

__all__ = [
    "BatchExportActionsFrame",
    "BatchInputFrame",
    "BatchResultsFrame",
    "HistoryHeaderFrame",
    "HistoryItemFrame",
    "HistoryListFrame",
    "HomeActionCardsFrame",
    "HomeInfoRowFrame",
    "HomeRecentRecordsFrame",
    "HomeStatusOverviewFrame",
    "HomeTipBarFrame",
    "HomeWelcomeFrame",
    "SettingsApiKeysSection",
    "SettingsExportSection",
    "SettingsLanguageSection",
    "SettingsPerformanceSection",
    "SettingsQuickActionsFrame",
    "SettingsSummarizerSection",
    "SettingsSystemSection",
    "SingleArticleInputFrame",
    "SingleArticleResultFrame",
    "SingleClipboardBannerFrame",
]
