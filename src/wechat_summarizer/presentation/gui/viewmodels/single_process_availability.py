"""Availability helpers for single-article processing options."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ports import ContainerLike


SUMMARIZER_DISPLAY_ORDER = ("simple", "ollama", "openai", "anthropic", "zhipu")
EXPORTER_DISPLAY_ORDER = ("html", "markdown", "obsidian", "notion", "onenote", "zip")

SUMMARIZER_UNAVAILABLE_REASONS = {
    "openai": "缺少 OPENAI_API_KEY",
    "anthropic": "缺少 ANTHROPIC_API_KEY",
    "zhipu": "缺少 ZHIPU_API_KEY",
    "ollama": "Ollama 服务不可用",
}
EXPORTER_UNAVAILABLE_REASONS = {
    "obsidian": "缺少 OBSIDIAN_VAULT_PATH",
    "notion": "缺少 NOTION_API_KEY 或 DATABASE_ID",
    "onenote": "缺少 ONENOTE_CLIENT_ID",
}


def get_available_summarizers(container: ContainerLike) -> list[tuple[str, bool, str]]:
    """Return configured summarizers in stable GUI display order."""
    return [
        (name, name in container.summarizers, get_summarizer_unavailable_reason(name))
        if name not in container.summarizers
        else (name, True, "")
        for name in SUMMARIZER_DISPLAY_ORDER
    ]


def get_available_exporters(container: ContainerLike) -> list[tuple[str, bool, str]]:
    """Return configured exporters in stable GUI display order."""
    return [
        (name, name in container.exporters, get_exporter_unavailable_reason(name))
        if name not in container.exporters
        else (name, True, "")
        for name in EXPORTER_DISPLAY_ORDER
    ]


def get_summarizer_unavailable_reason(name: str) -> str:
    """Return the user-facing unavailable reason for a summarizer."""
    return SUMMARIZER_UNAVAILABLE_REASONS.get(name, "未知原因")


def get_exporter_unavailable_reason(name: str) -> str:
    """Return the user-facing unavailable reason for an exporter."""
    return EXPORTER_UNAVAILABLE_REASONS.get(name, "未知原因")


__all__ = [
    "EXPORTER_DISPLAY_ORDER",
    "EXPORTER_UNAVAILABLE_REASONS",
    "SUMMARIZER_DISPLAY_ORDER",
    "SUMMARIZER_UNAVAILABLE_REASONS",
    "get_available_exporters",
    "get_available_summarizers",
    "get_exporter_unavailable_reason",
    "get_summarizer_unavailable_reason",
]
