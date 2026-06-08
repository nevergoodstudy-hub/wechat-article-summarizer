"""CI Python matrix guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_ci_matrix_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_ci_python_matrix.py"
    spec = importlib.util.spec_from_file_location("check_ci_python_matrix", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load CI matrix guard module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_ci_workflows_cover_required_python_matrix() -> None:
    """Current PR workflows must test Python 3.12, 3.13 and 3.14."""
    ci_matrix = _load_ci_matrix_module()

    assert ci_matrix.check_ci_python_matrix() == []


def test_inline_python_matrix_versions_are_extracted() -> None:
    """Inline GitHub Actions matrix syntax should be recognized."""
    ci_matrix = _load_ci_matrix_module()

    versions = ci_matrix.extract_python_matrix_versions(
        "strategy:\n  matrix:\n    python-version: ['3.11', '3.12', '3.13', '3.14']\n"
    )

    assert versions == frozenset({"3.11", "3.12", "3.13", "3.14"})


def test_multiline_python_matrix_versions_are_extracted() -> None:
    """Multiline GitHub Actions matrix syntax should be recognized."""
    ci_matrix = _load_ci_matrix_module()

    versions = ci_matrix.extract_python_matrix_versions(
        "strategy:\n"
        "  matrix:\n"
        "    python-version:\n"
        "      - '3.12'\n"
        "      - '3.13'\n"
        "      - '3.14'\n"
        "    os: [ubuntu-latest]\n"
    )

    assert versions == frozenset({"3.12", "3.13", "3.14"})


def test_missing_required_python_matrix_version_is_reported(tmp_path: Path) -> None:
    """Missing Python 3.13 must fail the guard."""
    ci_matrix = _load_ci_matrix_module()
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        "strategy:\n  matrix:\n    python-version: ['3.11', '3.12', '3.14']\n",
        encoding="utf-8",
    )

    violations = ci_matrix.check_ci_python_matrix((workflow,))

    assert len(violations) == 1
    assert violations[0].missing_versions == frozenset({"3.13"})
    assert "missing Python test matrix versions: 3.13" in violations[0].format()
