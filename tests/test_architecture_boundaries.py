"""Architecture boundary guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_architecture_module() -> ModuleType:
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "check_architecture_boundaries.py"
    )
    spec = importlib.util.spec_from_file_location("check_architecture_boundaries", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load architecture boundary module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_code_respects_architecture_boundaries() -> None:
    """The current codebase must respect the enforced import boundaries."""
    architecture = _load_architecture_module()

    assert architecture.check_boundaries() == []


def _use_fake_src_root(
    architecture: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Path:
    src_root = tmp_path / "src" / "wechat_summarizer"
    src_root.mkdir(parents=True)
    monkeypatch.setattr(architecture, "SRC_ROOT", src_root)
    return src_root


def test_domain_to_infrastructure_import_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Domain imports of infrastructure modules are violations."""
    architecture = _load_architecture_module()
    src_root = _use_fake_src_root(architecture, monkeypatch, tmp_path)
    sample = src_root / "domain" / "sample_for_boundary_check.py"
    sample.parent.mkdir()
    sample.write_text(
        "from wechat_summarizer.infrastructure.config import get_container\n",
        encoding="utf-8",
    )

    violations = architecture.check_boundaries([sample])

    assert len(violations) == 1
    assert violations[0].source_layer == "domain"
    assert violations[0].imported_module == "wechat_summarizer.infrastructure.config"


def test_application_to_presentation_relative_import_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Relative imports are normalized before boundary checks."""
    architecture = _load_architecture_module()
    src_root = _use_fake_src_root(architecture, monkeypatch, tmp_path)
    sample = src_root / "application" / "sample_for_boundary_check.py"
    sample.parent.mkdir()
    sample.write_text("from ..presentation.cli import run_cli\n", encoding="utf-8")

    violations = architecture.check_boundaries([sample])

    assert len(violations) == 1
    assert violations[0].source_layer == "application"
    assert violations[0].imported_module == "wechat_summarizer.presentation.cli"


def test_mcp_tooling_to_infrastructure_import_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """MCP tools/resources should receive services from the MCP composition root."""
    architecture = _load_architecture_module()
    src_root = _use_fake_src_root(architecture, monkeypatch, tmp_path)
    sample = src_root / "mcp" / "toolsets" / "sample_for_boundary_check.py"
    sample.parent.mkdir(parents=True)
    sample.write_text(
        "from ...infrastructure.config import get_container\n",
        encoding="utf-8",
    )

    violations = architecture.check_boundaries([sample])

    assert len(violations) == 1
    assert violations[0].source_layer == "mcp_tooling"
    assert violations[0].imported_module == "wechat_summarizer.infrastructure.config"


def test_presentation_to_infrastructure_import_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Presentation infrastructure imports are violations outside legacy allowlist."""
    architecture = _load_architecture_module()
    src_root = _use_fake_src_root(architecture, monkeypatch, tmp_path)
    sample = src_root / "presentation" / "gui" / "new_surface.py"
    sample.parent.mkdir(parents=True)
    sample.write_text(
        "from wechat_summarizer.infrastructure.adapters.exporters import HtmlExporter\n",
        encoding="utf-8",
    )

    violations = architecture.check_boundaries([sample])

    assert len(violations) == 1
    assert violations[0].source_layer == "presentation"
    assert violations[0].imported_module == "wechat_summarizer.infrastructure.adapters.exporters"
