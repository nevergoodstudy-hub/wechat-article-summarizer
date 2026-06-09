#!/usr/bin/env python3
"""Guard pytest layer markers and skip policy configuration."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
CONFTEST = ROOT / "tests" / "conftest.py"
REQUIRED_MARKERS = frozenset({"unit", "integration", "e2e", "slow"})


@dataclass(frozen=True)
class MarkerViolation:
    path: Path
    message: str

    def format(self) -> str:
        try:
            display_path = self.path.relative_to(ROOT)
        except ValueError:
            display_path = self.path
        return f"{display_path}: {self.message}"


def _extract_pytest_markers(pyproject_text: str) -> frozenset[str]:
    match = re.search(r"(?ms)^markers\s*=\s*\[(?P<body>.*?)^\]", pyproject_text)
    if match is None:
        return frozenset()

    markers: set[str] = set()
    for raw_marker in re.findall(r'"([^"]+)"', match.group("body")):
        marker_name = raw_marker.split(":", 1)[0].strip()
        if marker_name:
            markers.add(marker_name)
    return frozenset(markers)


def check_pytest_markers(
    *,
    pyproject_path: Path = PYPROJECT,
    conftest_path: Path = CONFTEST,
) -> list[MarkerViolation]:
    violations: list[MarkerViolation] = []
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    conftest_text = conftest_path.read_text(encoding="utf-8")

    registered_markers = _extract_pytest_markers(pyproject_text)
    missing_markers = REQUIRED_MARKERS - registered_markers
    if missing_markers:
        violations.append(
            MarkerViolation(
                pyproject_path,
                f"missing pytest marker registrations: {', '.join(sorted(missing_markers))}",
            )
        )

    if "--strict-markers" not in pyproject_text:
        violations.append(MarkerViolation(pyproject_path, "missing --strict-markers addopt"))

    required_conftest_tokens = (
        "layer_markers",
        "pytest.mark.unit",
        "RUN_INTEGRATION_TESTS",
        "RUN_E2E_TESTS",
    )
    for token in required_conftest_tokens:
        if token not in conftest_text:
            violations.append(MarkerViolation(conftest_path, f"missing test layer policy token: {token}"))

    return violations


def main() -> int:
    violations = check_pytest_markers()
    if violations:
        print("[pytest-markers] FAIL")
        for violation in violations:
            print(f"  - {violation.format()}")
        return 1

    print("[pytest-markers] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
