"""Reusable GUI frame sections."""

from .home_dashboard import (
    HomeActionCardsFrame,
    HomeTipBarFrame,
    HomeWelcomeFrame,
)
from .home_info import HomeInfoRowFrame, HomeRecentRecordsFrame, HomeStatusOverviewFrame

__all__ = [
    "HomeActionCardsFrame",
    "HomeInfoRowFrame",
    "HomeRecentRecordsFrame",
    "HomeStatusOverviewFrame",
    "HomeTipBarFrame",
    "HomeWelcomeFrame",
]
