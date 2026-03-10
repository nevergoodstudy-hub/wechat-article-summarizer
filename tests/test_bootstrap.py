"""组合根与入口注入回归测试。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from wechat_summarizer.bootstrap import AppRuntime, build_app_runtime
from wechat_summarizer.infrastructure.config.container import Container
from wechat_summarizer.presentation.cli.app import cli
from wechat_summarizer.presentation.gui import app as gui_app


def test_build_app_runtime_uses_explicit_container() -> None:
    container = Container.create_minimal()

    runtime = build_app_runtime(container=container)

    assert runtime.container is container
    assert runtime.settings is container.settings


def test_cli_prefers_injected_runtime() -> None:
    runner = CliRunner()
    mock_scraper = MagicMock()
    mock_scraper.name = "wechat_httpx"
    mock_summarizer = MagicMock()
    mock_summarizer.is_available.return_value = True
    mock_exporter = MagicMock()
    mock_exporter.is_available.return_value = True
    mock_container = MagicMock()
    mock_container.scrapers = [mock_scraper]
    mock_container.summarizers = {"simple": mock_summarizer}
    mock_container.exporters = {"markdown": mock_exporter}
    mock_container.storage = MagicMock()
    runtime = AppRuntime(settings=mock_container.settings, container=mock_container)

    with patch(
        "wechat_summarizer.presentation.cli.app.build_app_runtime",
        side_effect=AssertionError("should use injected runtime"),
    ):
        result = runner.invoke(cli, ["check"], obj=runtime)

    assert result.exit_code == 0
    assert "检查组件状态" in result.output


def test_run_gui_prefers_injected_runtime() -> None:
    runtime = AppRuntime(settings=MagicMock(), container=MagicMock())
    fake_app = MagicMock()

    with (
        patch.object(gui_app, "_ctk_available", True),
        patch.object(gui_app, "WechatSummarizerGUI", return_value=fake_app) as mock_gui,
        patch.object(
            gui_app,
            "build_app_runtime",
            side_effect=AssertionError("should use injected runtime"),
        ),
    ):
        gui_app.run_gui(runtime=runtime)

    mock_gui.assert_called_once_with(container=runtime.container, settings=runtime.settings)
    fake_app.run.assert_called_once_with()


def test_domain_boundary_script_passes_current_tree() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "check_domain_boundary.py"

    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert result.returncode == 0
    assert "No domain boundary violations found." in result.stdout
