"""Boundary protocols used by GUI view models."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol

from ....domain.entities import Article, Summary


class FetchArticleUseCaseLike(Protocol):
    """Minimal fetch use case surface required by GUI view models."""

    def execute(self, url: str, preferred_scraper: str | None = None) -> Article: ...


class SummarizeArticleUseCaseLike(Protocol):
    """Minimal summarize use case surface required by GUI view models."""

    def execute(
        self,
        article: Article,
        method: str = "simple",
        style: str = "concise",
        max_length: int = 500,
    ) -> Summary: ...


class ExportArticleUseCaseLike(Protocol):
    """Minimal export use case surface required by GUI view models."""

    def execute(
        self,
        article: Article,
        target: str,
        path: str | None = None,
        **options: Any,
    ) -> str: ...


class SecretValueLike(Protocol):
    """Secret value surface used for configuration status checks."""

    def get_secret_value(self) -> str: ...


class ProviderSettingsLike(Protocol):
    """LLM provider settings surface used by settings view model."""

    @property
    def api_key(self) -> SecretValueLike: ...


class ExportSettingsLike(Protocol):
    """Export settings surface used by settings view model."""

    @property
    def obsidian_vault_path(self) -> str: ...

    @property
    def notion_api_key(self) -> SecretValueLike: ...

    @property
    def notion_database_id(self) -> str: ...

    @property
    def onenote_client_id(self) -> str: ...


class AppSettingsLike(Protocol):
    """Settings surface required by GUI view models."""

    @property
    def default_summary_method(self) -> str: ...

    @property
    def openai(self) -> ProviderSettingsLike: ...

    @property
    def anthropic(self) -> ProviderSettingsLike: ...

    @property
    def zhipu(self) -> ProviderSettingsLike: ...

    @property
    def export(self) -> ExportSettingsLike: ...


class ContainerLike(Protocol):
    """Container capabilities consumed by GUI view models."""

    @property
    def fetch_use_case(self) -> FetchArticleUseCaseLike: ...

    @property
    def summarize_use_case(self) -> SummarizeArticleUseCaseLike: ...

    @property
    def export_use_case(self) -> ExportArticleUseCaseLike: ...

    @property
    def summarizers(self) -> Mapping[str, object]: ...

    @property
    def exporters(self) -> Mapping[str, object]: ...

    @property
    def storage(self) -> object | None: ...

    @property
    def settings(self) -> AppSettingsLike: ...
