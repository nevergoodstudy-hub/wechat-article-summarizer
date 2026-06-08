"""Pytest marker layering guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_pytest_markers_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_pytest_markers.py"
    spec = importlib.util.spec_from_file_location("check_pytest_markers", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load pytest marker guard module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_pytest_marker_policy_is_registered_and_guarded() -> None:
    """Current config must register all lifecycle markers and strict marker mode."""
    pytest_markers = _load_pytest_markers_module()

    assert pytest_markers.check_pytest_markers() == []


def test_pytest_marker_guard_reports_missing_e2e_marker(tmp_path: Path) -> None:
    """Missing e2e registration should fail the marker guard."""
    pytest_markers = _load_pytest_markers_module()
    pyproject = tmp_path / "pyproject.toml"
    conftest = tmp_path / "conftest.py"
    pyproject.write_text(
        "[tool.pytest.ini_options]\n"
        'addopts = ["--strict-markers"]\n'
        "markers = [\n"
        '  "slow: slow tests",\n'
        '  "integration: integration tests",\n'
        '  "unit: unit tests",\n'
        "]\n",
        encoding="utf-8",
    )
    conftest.write_text(
        "layer_markers = {'unit', 'integration', 'e2e'}\n"
        "pytest.mark.unit\n"
        "RUN_INTEGRATION_TESTS\n"
        "RUN_E2E_TESTS\n",
        encoding="utf-8",
    )

    violations = pytest_markers.check_pytest_markers(
        pyproject_path=pyproject,
        conftest_path=conftest,
    )

    assert len(violations) == 1
    assert "missing pytest marker registrations: e2e" in violations[0].format()


def test_pytest_marker_guard_reports_missing_default_unit_policy(tmp_path: Path) -> None:
    """The guard should prevent marker registration without collection policy."""
    pytest_markers = _load_pytest_markers_module()
    pyproject = tmp_path / "pyproject.toml"
    conftest = tmp_path / "conftest.py"
    pyproject.write_text(
        "[tool.pytest.ini_options]\n"
        'addopts = ["--strict-markers"]\n'
        "markers = [\n"
        '  "slow: slow tests",\n'
        '  "integration: integration tests",\n'
        '  "e2e: e2e tests",\n'
        '  "unit: unit tests",\n'
        "]\n",
        encoding="utf-8",
    )
    conftest.write_text("RUN_INTEGRATION_TESTS\nRUN_E2E_TESTS\n", encoding="utf-8")

    violations = pytest_markers.check_pytest_markers(
        pyproject_path=pyproject,
        conftest_path=conftest,
    )

    assert {violation.message for violation in violations} == {
        "missing test layer policy token: layer_markers",
        "missing test layer policy token: pytest.mark.unit",
    }
