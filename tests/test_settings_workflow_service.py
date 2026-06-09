"""Tests for settings workflow service."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from wechat_summarizer.features.settings_workflow import SettingsWorkflowService


@pytest.mark.unit
class TestSettingsWorkflowService:
    """Settings workflows should delegate infrastructure refreshes behind a facade."""

    def test_reload_summarizers_delegates_to_registry(self) -> None:
        registry = Mock()
        service = SettingsWorkflowService(registry)
        api_keys = {"openai": "sk-test", "deepseek": "ds-test"}

        service.reload_summarizers(api_keys)

        registry.reload_summarizers.assert_called_once_with(api_keys)
