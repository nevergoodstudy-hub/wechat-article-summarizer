"""Compatibility helpers for Python version differences."""

from __future__ import annotations

import sys
from enum import Enum

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:  # pragma: no cover - exercised only on Python 3.10

    class StrEnum(str, Enum):
        """Backport of enum.StrEnum for Python 3.10 compatibility."""
