"""Compatibility entrypoint for Word preview dialogs."""

from __future__ import annotations

from .word_preview_batch import show_batch_word_preview
from .word_preview_content import build_content_preview_with_images, extract_images_from_article
from .word_preview_single import show_word_preview

__all__ = [
    "build_content_preview_with_images",
    "extract_images_from_article",
    "show_batch_word_preview",
    "show_word_preview",
]
