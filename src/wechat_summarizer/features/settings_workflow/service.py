"""Feature service for settings workflows."""

from __future__ import annotations

from typing import Protocol


class SummarizerRegistryPort(Protocol):
    """Registry surface needed to reload summarizer adapters."""

    def reload_summarizers(self, api_keys: dict[str, str]) -> None: ...


class SettingsWorkflowService:
    """Application-facing service for settings-related workflows."""

    def __init__(self, summarizer_registry: SummarizerRegistryPort) -> None:
        self._summarizer_registry = summarizer_registry

    def reload_summarizers(self, api_keys: dict[str, str]) -> None:
        """Reload summarizers after API keys change."""
        self._summarizer_registry.reload_summarizers(api_keys)
