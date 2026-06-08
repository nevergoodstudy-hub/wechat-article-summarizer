"""Compatibility entrypoint for GUI form autosave."""

from __future__ import annotations

from .autosave_constants import (
    DEFAULT_DEBOUNCE_MS,
    DRAFT_EXPIRE_DAYS,
    MAX_DRAFT_SIZE,
    MAX_DRAFTS_PER_FORM,
    MAX_TOTAL_SIZE,
)
from .autosave_dialog import RestoreDialog, check_and_restore
from .autosave_encryptor import SimpleEncryptor
from .autosave_manager import AutoSaveManager
from .autosave_models import Draft, FormField
from .autosave_storage import DraftStorage

__all__ = [
    "DEFAULT_DEBOUNCE_MS",
    "DRAFT_EXPIRE_DAYS",
    "MAX_DRAFTS_PER_FORM",
    "MAX_DRAFT_SIZE",
    "MAX_TOTAL_SIZE",
    "AutoSaveManager",
    "Draft",
    "DraftStorage",
    "FormField",
    "RestoreDialog",
    "SimpleEncryptor",
    "check_and_restore",
]


if __name__ == "__main__":
    from .autosave_demo import run_autosave_demo

    run_autosave_demo()
