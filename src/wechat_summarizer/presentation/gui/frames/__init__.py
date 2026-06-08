"""Reusable GUI frame sections."""

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

__all__ = [
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
]
