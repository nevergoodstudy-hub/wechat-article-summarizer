"""Tests for the MCP composition root."""

from __future__ import annotations

import sys
import types

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from wechat_summarizer.infrastructure.config.container import override_container
from wechat_summarizer.mcp import server


class _FakeMCP:
    """Minimal FastMCP-like test double."""

    def sse_app(self) -> Starlette:
        async def healthcheck(_request):
            return JSONResponse({"ok": True})

        return Starlette(routes=[Route("/", healthcheck)])


class _FakeContainer:
    """Small container double that is compatible with reset_container teardown."""

    def __init__(self) -> None:
        self.article_workflow_service = object()
        self.analysis_workflow_service = object()

    def close(self) -> None:
        pass


@pytest.mark.unit
class TestMCPServerComposition:
    """Composition-root behavior should stay thin and explicit."""

    def test_register_tools_delegates_to_composable_toolsets(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[tuple[str, object]] = []
        fake_mcp = _FakeMCP()
        fake_container = _FakeContainer()

        monkeypatch.setattr(
            server,
            "register_article_tools",
            lambda mcp, factory: calls.append(("article", factory())),
        )
        monkeypatch.setattr(
            server,
            "register_analysis_tools",
            lambda mcp, factory: calls.append(("analysis", factory())),
        )

        with override_container(fake_container):  # type: ignore[arg-type]
            server._register_tools(fake_mcp)

        assert calls == [
            ("article", fake_container.article_workflow_service),
            ("analysis", fake_container.analysis_workflow_service),
        ]

    def test_register_resources_delegates_to_composable_resources(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        calls: list[tuple[str, object]] = []
        fake_mcp = _FakeMCP()
        fake_container = _FakeContainer()

        monkeypatch.setattr(
            server,
            "register_article_resources",
            lambda mcp, factory: calls.append(("resources", factory())),
        )

        with override_container(fake_container):  # type: ignore[arg-type]
            server._register_resources(fake_mcp)

        assert calls == [("resources", fake_container.article_workflow_service)]

    def test_ensure_mcp_initializes_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_mcp = _FakeMCP()
        calls: list[str] = []

        monkeypatch.setattr(server, "mcp", None)
        monkeypatch.setattr(server, "_get_mcp", lambda: fake_mcp)
        monkeypatch.setattr(server, "_register_tools", lambda mcp: calls.append("tools"))
        monkeypatch.setattr(server, "_register_resources", lambda mcp: calls.append("resources"))

        first = server._ensure_mcp()
        second = server._ensure_mcp()

        assert first is fake_mcp
        assert second is fake_mcp
        assert calls == ["tools", "resources"]

    def test_build_http_app_rejects_missing_token(self) -> None:
        app = server.build_http_app(_FakeMCP(), auth_token="secret-token")
        client = TestClient(app)

        response = client.get("/mcp/")

        assert response.status_code == 401
        assert response.json()["error"] == "Unauthorized"

    def test_build_http_app_allows_authorized_request(self) -> None:
        app = server.build_http_app(_FakeMCP(), auth_token="secret-token")
        client = TestClient(app)

        response = client.get("/mcp/", headers={"x-mcp-token": "secret-token"})

        assert response.status_code == 200
        assert response.json() == {"ok": True}

    def test_run_mcp_server_rejects_remote_http_without_explicit_opt_in(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(server, "_ensure_mcp", lambda: _FakeMCP())

        with pytest.raises(ValueError, match="远程监听已被禁止"):
            server.run_mcp_server(transport="http", host="0.0.0.0")

    def test_run_mcp_server_rejects_remote_http_without_token(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(server, "_ensure_mcp", lambda: _FakeMCP())

        with pytest.raises(ValueError, match="必须配置认证 token"):
            server.run_mcp_server(transport="http", host="0.0.0.0", allow_remote=True)

    def test_run_mcp_server_http_invokes_uvicorn_with_built_app(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}
        fake_mcp = _FakeMCP()
        fake_app = Starlette()

        class _FakeUvicorn:
            @staticmethod
            def run(app, host: str, port: int) -> None:
                captured["app"] = app
                captured["host"] = host
                captured["port"] = port

        monkeypatch.setattr(server, "_ensure_mcp", lambda: fake_mcp)
        monkeypatch.setattr(server, "build_http_app", lambda mcp, auth_token=None: fake_app)
        monkeypatch.setitem(sys.modules, "uvicorn", types.SimpleNamespace(run=_FakeUvicorn.run))

        server.run_mcp_server(
            transport="http",
            host="127.0.0.1",
            port=8765,
            auth_token="token",
        )

        assert captured == {"app": fake_app, "host": "127.0.0.1", "port": 8765}

    def test_run_mcp_server_remote_http_requires_token_before_uvicorn(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured: dict[str, object] = {}
        fake_mcp = _FakeMCP()
        fake_app = Starlette()

        class _FakeUvicorn:
            @staticmethod
            def run(app, host: str, port: int) -> None:
                captured["app"] = app
                captured["host"] = host
                captured["port"] = port

        monkeypatch.setattr(server, "_ensure_mcp", lambda: fake_mcp)
        monkeypatch.setattr(server, "build_http_app", lambda mcp, auth_token=None: fake_app)
        monkeypatch.setitem(sys.modules, "uvicorn", types.SimpleNamespace(run=_FakeUvicorn.run))

        server.run_mcp_server(
            transport="http",
            host="0.0.0.0",
            port=8765,
            auth_token="token",
            allow_remote=True,
        )

        assert captured == {"app": fake_app, "host": "0.0.0.0", "port": 8765}
