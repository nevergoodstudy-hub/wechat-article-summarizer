"""Translation text sanitization helpers."""

from __future__ import annotations

import html
import re


def sanitize_translation_text(text: str) -> str:
    """Escape translation text and strip dangerous inline handlers."""
    safe_text = html.escape(text)
    safe_text = re.sub(
        r"<script[^>]*>.*?</script>",
        "",
        safe_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return re.sub(r"on\w+\s*=", "", safe_text, flags=re.IGNORECASE)


__all__ = ["sanitize_translation_text"]
