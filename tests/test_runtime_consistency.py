from __future__ import annotations

import re
from pathlib import Path

import pytest
from click.testing import CliRunner

from wechat_summarizer.infrastructure.config import settings as settings_module
from wechat_summarizer.infrastructure.config.settings import get_settings, reset_settings
from wechat_summarizer.mcp.a2a import create_wechat_summarizer_agent_card
from wechat_summarizer.presentation.cli.app import cli
from wechat_summarizer.shared.constants import VERSION


def _read_pyproject_version() -> str:
    pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'(?ms)^\[project\].*?^version\s*=\s*"([^"]+)"', pyproject_text)
    assert match is not None
    return match.group(1)


@pytest.mark.unit
def test_shared_version_matches_pyproject() -> None:
    assert _read_pyproject_version() == VERSION


@pytest.mark.unit
def test_agent_card_uses_shared_version() -> None:
    assert create_wechat_summarizer_agent_card().version == VERSION


@pytest.mark.unit
def test_get_settings_reads_stable_user_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_env = tmp_path / ".env"
    config_env.write_text(
        "WECHAT_SUMMARIZER_OPENAI__MODEL=config-model\n",
        encoding="utf-8",
    )

    other_dir = tmp_path / "other"
    other_dir.mkdir()
    monkeypatch.chdir(other_dir)
    monkeypatch.setattr(settings_module, "get_env_file_candidates", lambda: (config_env,))

    reset_settings()
    settings = get_settings()

    assert settings.openai.model == "config-model"


@pytest.mark.unit
def test_get_settings_allows_checkout_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    config_env = tmp_path / "config.env"
    config_env.write_text(
        "WECHAT_SUMMARIZER_OPENAI__MODEL=config-model\n",
        encoding="utf-8",
    )
    cwd_env = tmp_path / "cwd.env"
    cwd_env.write_text(
        "WECHAT_SUMMARIZER_OPENAI__MODEL=override-model\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        settings_module,
        "get_env_file_candidates",
        lambda: (config_env, cwd_env),
    )

    reset_settings()
    settings = get_settings()

    assert settings.openai.model == "override-model"


@pytest.mark.unit
def test_config_init_writes_to_stable_env_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from wechat_summarizer.presentation.cli import app as cli_app

    env_path = tmp_path / ".env"
    monkeypatch.setattr(cli_app, "get_env_file_path", lambda: env_path)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["config-init"],
        input="\n\n\n\n",
    )

    assert result.exit_code == 0
    assert env_path.exists()
    assert "WECHAT_SUMMARIZER_OLLAMA__HOST=http://localhost:11434" in env_path.read_text(
        encoding="utf-8"
    )
