#!/usr/bin/env python3
"""Guard GitHub Actions Python test matrix coverage.

The renewal checklist requires the CI test matrix to cover Python 3.12 through
3.14. The project also keeps Python 3.11 in the matrix as the declared minimum
runtime, but the guard focuses on the P2 acceptance requirement.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_FILES = (
    ROOT / ".github" / "workflows" / "ci.yml",
    ROOT / ".github" / "workflows" / "build.yml",
)
REQUIRED_PYTHON_VERSIONS = frozenset({"3.12", "3.13", "3.14"})
VERSION_RE = re.compile(r"['\"]?(\d+\.\d+)['\"]?")


@dataclass(frozen=True)
class MatrixViolation:
    path: Path
    missing_versions: frozenset[str]
    found_versions: frozenset[str]

    def format(self) -> str:
        try:
            relative = self.path.relative_to(ROOT).as_posix()
        except ValueError:
            relative = self.path.as_posix()
        missing = ", ".join(sorted(self.missing_versions))
        found = ", ".join(sorted(self.found_versions)) or "<none>"
        return f"{relative}: missing Python test matrix versions: {missing}; found: {found}"


def _indent_width(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _extract_inline_versions(value: str) -> set[str]:
    return set(VERSION_RE.findall(value))


def extract_python_matrix_versions(text: str) -> frozenset[str]:
    """Extract versions declared under GitHub Actions matrix python-version keys."""
    lines = text.splitlines()
    versions: set[str] = set()

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("python-version:"):
            continue

        _, value = stripped.split(":", 1)
        versions.update(_extract_inline_versions(value))
        if value.strip():
            continue

        parent_indent = _indent_width(line)
        for child in lines[index + 1 :]:
            if not child.strip():
                continue
            if _indent_width(child) <= parent_indent:
                break
            child_stripped = child.strip()
            if child_stripped.startswith("-"):
                versions.update(_extract_inline_versions(child_stripped))

    return frozenset(versions)


def check_ci_python_matrix(paths: tuple[Path, ...] = WORKFLOW_FILES) -> list[MatrixViolation]:
    """Return workflow files that do not cover the required Python matrix."""
    violations: list[MatrixViolation] = []

    for path in paths:
        versions = extract_python_matrix_versions(path.read_text(encoding="utf-8"))
        missing = REQUIRED_PYTHON_VERSIONS - versions
        if missing:
            violations.append(
                MatrixViolation(
                    path=path,
                    missing_versions=frozenset(missing),
                    found_versions=versions,
                )
            )

    return violations


def main() -> int:
    violations = check_ci_python_matrix()
    if not violations:
        print("[ci-python-matrix] PASS")
        return 0

    print("[ci-python-matrix] FAIL")
    for violation in violations:
        print(violation.format())
    return 1


if __name__ == "__main__":
    sys.exit(main())
