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
