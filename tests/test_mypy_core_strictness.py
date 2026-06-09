"""Mypy core strictness guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_mypy_guard_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_mypy_core_strictness.py"
    spec = importlib.util.spec_from_file_location("check_mypy_core_strictness", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load mypy strictness guard module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_pyproject_enforces_core_mypy_strictness() -> None:
    """Current config must keep domain/application under stricter mypy checks."""
    mypy_guard = _load_mypy_guard_module()

    assert mypy_guard.check_mypy_core_strictness() == []


def test_missing_core_override_is_reported(tmp_path: Path) -> None:
    """A pyproject without the core override must fail the guard."""
    mypy_guard = _load_mypy_guard_module()
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.mypy]\npython_version = '3.14'\n",
        encoding="utf-8",
    )

    violations = mypy_guard.check_mypy_core_strictness(pyproject)

    assert len(violations) == 1
    assert "missing core mypy override" in violations[0].format()


def test_weakened_core_flag_is_reported(tmp_path: Path) -> None:
    """Relaxing a required strictness flag must fail the guard."""
    mypy_guard = _load_mypy_guard_module()
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[[tool.mypy.overrides]]\n"
        "module = ['wechat_summarizer.domain.*', 'wechat_summarizer.application.*']\n"
        "disallow_untyped_defs = false\n"
        "check_untyped_defs = true\n"
        "warn_return_any = true\n"
        "strict_equality = true\n",
        encoding="utf-8",
    )

    violations = mypy_guard.check_mypy_core_strictness(pyproject)

    assert len(violations) == 1
    assert "disallow_untyped_defs" in violations[0].format()
