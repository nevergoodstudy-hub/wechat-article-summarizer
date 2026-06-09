"""Test filesystem isolation guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_isolation_module() -> ModuleType:
    module_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "check_test_filesystem_isolation.py"
    )
    spec = importlib.util.spec_from_file_location("check_test_filesystem_isolation", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load test filesystem isolation module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_tests_use_tmp_path_for_filesystem_side_effects() -> None:
    """Current tests should not bypass pytest tmp_path isolation."""
    isolation = _load_isolation_module()

    assert isolation.check_tests() == []


def test_tempfile_import_is_reported(tmp_path: Path) -> None:
    """Tests should use tmp_path instead of tempfile helpers."""
    isolation = _load_isolation_module()
    sample = tmp_path / "test_tempfile_usage.py"
    sample.write_text(
        "import tempfile\n\ndef test_bad():\n    tempfile.TemporaryDirectory()\n",
        encoding="utf-8",
    )

    violations = isolation.check_tests([sample])

    assert len(violations) == 2
    assert "importing tempfile" in violations[0].message
    assert "TemporaryDirectory" in violations[1].message


def test_path_home_call_is_reported(tmp_path: Path) -> None:
    """Tests should patch home-dependent code to tmp_path."""
    isolation = _load_isolation_module()
    sample = tmp_path / "test_home_usage.py"
    sample.write_text(
        "from pathlib import Path\n\ndef test_bad():\n    return Path.home() / '.app'\n",
        encoding="utf-8",
    )

    violations = isolation.check_tests([sample])

    assert len(violations) == 1
    assert "Path.home" in violations[0].message


def test_tmp_path_usage_is_allowed(tmp_path: Path) -> None:
    """tmp_path-backed file writes are the preferred isolated pattern."""
    isolation = _load_isolation_module()
    sample = tmp_path / "test_tmp_path_usage.py"
    sample.write_text(
        "from pathlib import Path\n"
        "\n"
        "def test_good(tmp_path: Path):\n"
        "    (tmp_path / 'file.txt').write_text('ok')\n",
        encoding="utf-8",
    )

    assert isolation.check_tests([sample]) == []


def test_unscoped_click_isolated_filesystem_is_reported(tmp_path: Path) -> None:
    """Click isolated filesystems should be rooted in pytest tmp_path."""
    isolation = _load_isolation_module()
    sample = tmp_path / "test_click_usage.py"
    sample.write_text(
        "def test_bad(runner):\n    with runner.isolated_filesystem():\n        pass\n",
        encoding="utf-8",
    )

    violations = isolation.check_tests([sample])

    assert len(violations) == 1
    assert "temp_dir" in violations[0].message
