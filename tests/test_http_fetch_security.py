"""HTTP fetch security guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_http_fetch_security_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_http_fetch_security.py"
    spec = importlib.util.spec_from_file_location("check_http_fetch_security", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load HTTP fetch security module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_user_fetch_surfaces_use_safe_fetch_helpers() -> None:
    """Current scraper/exporter user URL surfaces should use SSRF-safe helpers."""
    http_fetch_security = _load_http_fetch_security_module()

    assert http_fetch_security.check_http_fetch_security() == []


def test_direct_httpx_client_is_reported(tmp_path: Path) -> None:
    """Direct httpx clients bypass the per-hop redirect validation policy."""
    http_fetch_security = _load_http_fetch_security_module()
    sample = tmp_path / "unsafe_fetch.py"
    sample.write_text(
        "import httpx\n\n"
        "def fetch(url: str):\n"
        "    with httpx.Client(follow_redirects=True) as client:\n"
        "        return client.get(url)\n",
        encoding="utf-8",
    )

    violations = http_fetch_security.check_http_fetch_security([sample])

    assert len(violations) == 1
    assert "safe_fetch" in violations[0].message


def test_top_level_httpx_fetch_is_reported(tmp_path: Path) -> None:
    """Top-level httpx helpers also bypass the shared network policy."""
    http_fetch_security = _load_http_fetch_security_module()
    sample = tmp_path / "unsafe_top_level_fetch.py"
    sample.write_text(
        "import httpx\n\ndef fetch(url: str):\n    return httpx.get(url)\n",
        encoding="utf-8",
    )

    violations = http_fetch_security.check_http_fetch_security([sample])

    assert len(violations) == 1
    assert "top-level httpx" in violations[0].message


def test_safe_fetch_usage_is_allowed(tmp_path: Path) -> None:
    """safe_fetch helpers implement the per-hop validation contract."""
    http_fetch_security = _load_http_fetch_security_module()
    sample = tmp_path / "safe_fetch.py"
    sample.write_text(
        "from wechat_summarizer.shared.utils.ssrf_protection import safe_fetch_sync\n\n"
        "def fetch(url: str):\n"
        "    return safe_fetch_sync(url)\n",
        encoding="utf-8",
    )

    assert http_fetch_security.check_http_fetch_security([sample]) == []
