"""Domain boundary guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_domain_boundary_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_domain_boundary.py"
    spec = importlib.util.spec_from_file_location("check_domain_boundary", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load domain boundary module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _use_fake_src_root(
    domain_boundary: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Path:
    src_root = tmp_path / "src" / "wechat_summarizer"
    domain_root = src_root / "domain"
    domain_root.mkdir(parents=True)
    monkeypatch.setattr(domain_boundary, "SRC_ROOT", src_root)
    monkeypatch.setattr(domain_boundary, "DOMAIN_ROOT", domain_root)
    return src_root


def test_current_domain_respects_boundary() -> None:
    """The current domain layer must not import outer project layers."""
    domain_boundary = _load_domain_boundary_module()

    assert domain_boundary.check_domain_boundary() == []


def test_domain_to_infrastructure_import_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Domain imports of infrastructure modules are violations."""
    domain_boundary = _load_domain_boundary_module()
    src_root = _use_fake_src_root(domain_boundary, monkeypatch, tmp_path)
    sample = src_root / "domain" / "sample_for_domain_boundary.py"
    sample.write_text(
        "from wechat_summarizer.infrastructure.config import get_container\n",
        encoding="utf-8",
    )

    violations = domain_boundary.check_domain_boundary([sample])

    assert len(violations) == 1
    assert violations[0].imported_module == "wechat_summarizer.infrastructure.config"
    assert "domain layer must not import" in violations[0].format()


def test_domain_to_presentation_relative_import_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Relative imports are normalized before checking the domain boundary."""
    domain_boundary = _load_domain_boundary_module()
    src_root = _use_fake_src_root(domain_boundary, monkeypatch, tmp_path)
    sample = src_root / "domain" / "entities" / "sample_for_domain_boundary.py"
    sample.parent.mkdir()
    sample.write_text("from ...presentation.cli import app\n", encoding="utf-8")

    violations = domain_boundary.check_domain_boundary([sample])

    assert len(violations) == 1
    assert violations[0].imported_module == "wechat_summarizer.presentation.cli"


def test_domain_internal_import_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Domain modules can import other domain modules."""
    domain_boundary = _load_domain_boundary_module()
    src_root = _use_fake_src_root(domain_boundary, monkeypatch, tmp_path)
    sample = src_root / "domain" / "entities" / "sample_for_domain_boundary.py"
    sample.parent.mkdir()
    sample.write_text("from ..value_objects.url import ArticleURL\n", encoding="utf-8")

    assert domain_boundary.check_domain_boundary([sample]) == []


def test_standard_library_import_is_allowed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The guard only blocks outer project layers."""
    domain_boundary = _load_domain_boundary_module()
    src_root = _use_fake_src_root(domain_boundary, monkeypatch, tmp_path)
    sample = src_root / "domain" / "sample_for_domain_boundary.py"
    sample.write_text("from datetime import datetime\nimport uuid\n", encoding="utf-8")

    assert domain_boundary.check_domain_boundary([sample]) == []
