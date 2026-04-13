"""Tests for package entrypoints."""

from __future__ import annotations

import builtins
import sys

import pytest

from wechat_summarizer import __main__ as package_main
from wechat_summarizer.mcp import __main__ as mcp_main
from wechat_summarizer.presentation import cli as cli_module
from wechat_summarizer.presentation import gui as gui_module


@pytest.mark.unit
class TestPackageMain:
    """Tests for ``python -m wechat_summarizer``."""

    def test_main_defaults_to_gui_without_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        monkeypatch.setattr(package_main, "setup_logger", lambda: calls.append("logger"))
        monkeypatch.setattr(package_main, "_run_gui_or_exit", lambda: calls.append("gui"))
        monkeypatch.setattr(package_main.sys, "argv", ["wechat_summarizer"])

        package_main.main()

        assert calls == ["logger", "gui"]

    def test_main_explicit_gui_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        monkeypatch.setattr(package_main, "setup_logger", lambda: calls.append("logger"))
        monkeypatch.setattr(package_main, "_run_gui_or_exit", lambda: calls.append("gui"))
        monkeypatch.setattr(package_main.sys, "argv", ["wechat_summarizer", "gui"])

        package_main.main()

        assert calls == ["logger", "gui"]

    def test_main_legacy_cli_prefix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        monkeypatch.setattr(package_main, "setup_logger", lambda: calls.append("logger"))
        monkeypatch.setattr(cli_module, "run_cli", lambda: calls.append("cli"))
        monkeypatch.setattr(package_main.sys, "argv", ["wechat_summarizer", "cli", "fetch"])

        package_main.main()

        assert calls == ["logger", "cli"]
        assert package_main.sys.argv == ["wechat_summarizer", "fetch"]

    def test_main_routes_other_commands_to_cli(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        monkeypatch.setattr(package_main, "setup_logger", lambda: calls.append("logger"))
        monkeypatch.setattr(cli_module, "run_cli", lambda: calls.append("cli"))
        monkeypatch.setattr(
            package_main.sys,
            "argv",
            ["wechat_summarizer", "fetch", "https://mp.weixin.qq.com/s/demo"],
        )

        package_main.main()

        assert calls == ["logger", "cli"]

    def test_run_gui_or_exit_runs_gui(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        monkeypatch.setattr(gui_module, "run_gui", lambda: calls.append("run_gui"))

        package_main._run_gui_or_exit()

        assert calls == ["run_gui"]

    def test_run_gui_or_exit_prints_helpful_message_on_import_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
            if name.endswith("presentation.gui") or (
                name.endswith("presentation") and "gui" in fromlist
            ):
                raise ImportError("missing gui extras")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        with pytest.raises(SystemExit) as exc_info:
            package_main._run_gui_or_exit()

        captured = capsys.readouterr()
        assert exc_info.value.code == 1
        assert "GUI" in captured.out
        assert "--help" in captured.out


@pytest.mark.unit
class TestMCPMain:
    """Tests for ``python -m wechat_summarizer.mcp``."""

    def test_main_uses_default_arguments(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[dict[str, object]] = []

        monkeypatch.setattr(
            mcp_main,
            "run_mcp_server",
            lambda **kwargs: calls.append(kwargs),
        )
        monkeypatch.setattr(sys, "argv", ["wechat_summarizer.mcp"])

        mcp_main.main()

        assert calls == [
            {
                "transport": "stdio",
                "port": 8000,
                "host": "127.0.0.1",
                "auth_token": None,
                "allow_remote": False,
            }
        ]

    def test_main_reads_env_token_when_argument_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[dict[str, object]] = []

        monkeypatch.setattr(
            mcp_main,
            "run_mcp_server",
            lambda **kwargs: calls.append(kwargs),
        )
        monkeypatch.setenv("WECHAT_SUMMARIZER_MCP_AUTH_TOKEN", "env-token")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "wechat_summarizer.mcp",
                "--transport",
                "http",
                "--port",
                "9000",
                "--host",
                "0.0.0.0",
                "--allow-remote",
            ],
        )

        mcp_main.main()

        assert calls == [
            {
                "transport": "http",
                "port": 9000,
                "host": "0.0.0.0",
                "auth_token": "env-token",
                "allow_remote": True,
            }
        ]

    def test_main_prefers_explicit_auth_token_argument(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[dict[str, object]] = []

        monkeypatch.setattr(
            mcp_main,
            "run_mcp_server",
            lambda **kwargs: calls.append(kwargs),
        )
        monkeypatch.setenv("WECHAT_SUMMARIZER_MCP_AUTH_TOKEN", "env-token")
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "wechat_summarizer.mcp",
                "--auth-token",
                "cli-token",
            ],
        )

        mcp_main.main()

        assert calls[0]["auth_token"] == "cli-token"
