#!/usr/bin/env python3
"""Guard gradual mypy strictness for core modules."""

from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
CORE_MODULES = frozenset(
    {
        "wechat_summarizer.domain.*",
        "wechat_summarizer.application.*",
    }
)
REQUIRED_FLAGS = {
    "disallow_untyped_defs": True,
    "check_untyped_defs": True,
    "warn_return_any": True,
    "strict_equality": True,
}


@dataclass(frozen=True)
class StrictnessViolation:
    message: str

    def format(self) -> str:
        return f"pyproject.toml: {self.message}"


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return [value]


def _load_mypy_config(path: Path = PYPROJECT) -> dict[str, Any]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    tool = data.get("tool", {})
    if not isinstance(tool, dict):
        return {}
    mypy = tool.get("mypy", {})
    return mypy if isinstance(mypy, dict) else {}


def check_mypy_core_strictness(path: Path = PYPROJECT) -> list[StrictnessViolation]:
    """Return missing or weakened core mypy strictness settings."""
    mypy = _load_mypy_config(path)
    overrides = mypy.get("overrides", [])
    if not isinstance(overrides, list):
        return [StrictnessViolation("tool.mypy.overrides must be a list")]

    for override in overrides:
        if not isinstance(override, dict):
            continue
        modules = {str(module) for module in _as_list(override.get("module", []))}
        if not CORE_MODULES.issubset(modules):
            continue

        violations = [
            StrictnessViolation(f"core override must set {name} = {expected!r}")
            for name, expected in REQUIRED_FLAGS.items()
            if override.get(name) is not expected
        ]
        return violations

    modules = ", ".join(sorted(CORE_MODULES))
    return [StrictnessViolation(f"missing core mypy override for {modules}")]


def main() -> int:
    violations = check_mypy_core_strictness()
    if not violations:
        print("[mypy-core-strictness] PASS")
        return 0

    print("[mypy-core-strictness] FAIL")
    for violation in violations:
        print(violation.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
