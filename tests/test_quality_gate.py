"""Quality gate script regression tests."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


def _load_quality_gate_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "quality_gate.py"
    spec = importlib.util.spec_from_file_location("quality_gate", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load quality_gate module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_quality_gate_pass_message_is_ascii(capsys) -> None:
    """PASS 消息应保持 ASCII 安全，避免 Windows GBK 控制台崩溃。"""
    quality_gate = _load_quality_gate_module()

    with (
        patch.object(quality_gate, "parse_args", return_value=argparse.Namespace(mode="lint")),
        patch.object(quality_gate, "run_lint"),
    ):
        assert quality_gate.main() == 0

    output = capsys.readouterr().out
    assert "[quality-gate] PASS" in output
    assert "✅" not in output


def test_quality_gate_fail_message_is_ascii(capsys) -> None:
    """FAIL 消息应保持 ASCII 安全，避免 Windows GBK 控制台崩溃。"""
    quality_gate = _load_quality_gate_module()

    with (
        patch.object(quality_gate, "parse_args", return_value=argparse.Namespace(mode="lint")),
        patch.object(quality_gate, "run_lint", side_effect=quality_gate.GateError("boom")),
    ):
        assert quality_gate.main() == 1

    output = capsys.readouterr().out
    assert "[quality-gate] FAIL: boom" in output
    assert "❌" not in output


def test_quality_gate_phase_a_runs_acceptance_pack() -> None:
    """Phase A mode should remain a single acceptance entrypoint."""
    quality_gate = _load_quality_gate_module()
    calls: list[str] = []

    with (
        patch.object(
            quality_gate,
            "parse_args",
            return_value=argparse.Namespace(mode="phase-a"),
        ),
        patch.object(quality_gate, "run_phase_a", side_effect=lambda: calls.append("phase-a")),
    ):
        assert quality_gate.main() == 0

    assert calls == ["phase-a"]


def test_quality_gate_all_includes_phase_a_acceptance() -> None:
    """The default full gate should keep Phase A acceptance in the chain."""
    quality_gate = _load_quality_gate_module()
    calls: list[str] = []

    with (
        patch.object(quality_gate, "parse_args", return_value=argparse.Namespace(mode="all")),
        patch.object(quality_gate, "run_lint", side_effect=lambda: calls.append("lint")),
        patch.object(
            quality_gate,
            "run_architecture",
            side_effect=lambda: calls.append("architecture"),
        ),
        patch.object(
            quality_gate,
            "run_test_executability",
            side_effect=lambda: calls.append("test-executability"),
        ),
        patch.object(quality_gate, "run_mypy", side_effect=lambda: calls.append("mypy")),
        patch.object(quality_gate, "run_tests", side_effect=lambda: calls.append("test")),
        patch.object(
            quality_gate,
            "run_security_smoke",
            side_effect=lambda: calls.append("security-smoke"),
        ),
        patch.object(quality_gate, "run_phase_a", side_effect=lambda: calls.append("phase-a")),
    ):
        assert quality_gate.main() == 0

    assert calls == [
        "lint",
        "architecture",
        "test-executability",
        "mypy",
        "test",
        "security-smoke",
        "phase-a",
    ]
