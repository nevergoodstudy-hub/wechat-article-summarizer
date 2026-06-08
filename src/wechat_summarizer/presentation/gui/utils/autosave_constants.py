"""Constants for GUI form autosave."""

from __future__ import annotations

MAX_DRAFT_SIZE = 100 * 1024
MAX_TOTAL_SIZE = 5 * 1024 * 1024
MAX_DRAFTS_PER_FORM = 10
DRAFT_EXPIRE_DAYS = 7
DEFAULT_DEBOUNCE_MS = 300


__all__ = [
    "DEFAULT_DEBOUNCE_MS",
    "DRAFT_EXPIRE_DAYS",
    "MAX_DRAFTS_PER_FORM",
    "MAX_DRAFT_SIZE",
    "MAX_TOTAL_SIZE",
]
