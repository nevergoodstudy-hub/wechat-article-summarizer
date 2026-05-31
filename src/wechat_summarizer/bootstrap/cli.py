"""CLI composition root."""

from __future__ import annotations

from typing import Any

from ..infrastructure.adapters.wechat_batch import (
    ArticleListCache,
    FileCredentialStorage,
    LinkExporter,
    WechatArticleFetcher,
    WechatAuthManager,
)
from ..infrastructure.config import get_container, get_settings
from ..presentation.cli import app as cli_app
from ..presentation.cli import batch_commands


def build_wechat_batch_components() -> dict[str, Any]:
    """Assemble WeChat public-account batch command adapters."""
    storage = FileCredentialStorage()
    auth = WechatAuthManager(storage)
    cache = ArticleListCache()

    return {
        "storage": storage,
        "auth": auth,
        "fetcher": WechatArticleFetcher(auth, cache=cache),
        "cache": cache,
        "exporter": LinkExporter(),
    }


def configure_cli_runtime() -> None:
    """Install infrastructure providers used by CLI presentation commands."""
    cli_app.configure_runtime(
        container_provider=get_container,
        settings_provider=get_settings,
    )
    batch_commands.configure_components_factory(build_wechat_batch_components)


def run_cli() -> None:
    """Run the CLI with infrastructure dependencies assembled."""
    configure_cli_runtime()
    cli_app.run_cli()
