#!/usr/bin/env python3
"""Guard architecture decision records."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_DIR = ROOT / "docs" / "adr"
REQUIRED_SECTIONS = (
    "## Status",
    "## Context",
    "## Decision",
    "## Rationale",
    "## Trade-offs",
    "## Consequences",
)
ADR_NAME_PATTERN = re.compile(r"^\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
ACCEPTED_STATUSES = {"Proposed", "Accepted", "Deprecated", "Superseded"}


@dataclass(frozen=True)
class AdrViolation:
    path: Path
    message: str

    def format(self) -> str:
        try:
            display_path = self.path.relative_to(ROOT)
        except ValueError:
            display_path = self.path
        return f"{display_path}: {self.message}"


def _extract_status(text: str) -> str | None:
    match = re.search(r"(?ms)^## Status\s*\n(?P<status>[^\n#]+)", text)
    if match is None:
        return None
    return match.group("status").strip().split(" ", 1)[0]


def check_adr_docs(adr_dir: Path = ADR_DIR) -> list[AdrViolation]:
    violations: list[AdrViolation] = []
    if not adr_dir.exists():
        return [AdrViolation(adr_dir, "ADR directory is missing")]

    adr_files = sorted(path for path in adr_dir.glob("*.md") if path.name != "README.md")
    if not adr_files:
        return [AdrViolation(adr_dir, "no ADR files found")]

    readme = adr_dir / "README.md"
    if not readme.exists():
        violations.append(AdrViolation(readme, "ADR index is missing"))
        readme_text = ""
    else:
        readme_text = readme.read_text(encoding="utf-8")

    for adr_file in adr_files:
        if ADR_NAME_PATTERN.match(adr_file.name) is None:
            violations.append(AdrViolation(adr_file, "ADR filename must match 000-kebab-case.md"))

        text = adr_file.read_text(encoding="utf-8")
        if not text.startswith("# ADR-"):
            violations.append(AdrViolation(adr_file, "ADR title must start with '# ADR-'"))
        for section in REQUIRED_SECTIONS:
            if section not in text:
                violations.append(AdrViolation(adr_file, f"missing required section: {section}"))

        status = _extract_status(text)
        if status not in ACCEPTED_STATUSES:
            violations.append(
                AdrViolation(
                    adr_file,
                    f"invalid or missing status; expected one of {', '.join(sorted(ACCEPTED_STATUSES))}",
                )
            )

        if adr_file.name not in readme_text:
            violations.append(AdrViolation(readme, f"ADR index missing entry for {adr_file.name}"))

    return violations


def main() -> int:
    violations = check_adr_docs()
    if violations:
        print("[adr-docs] FAIL")
        for violation in violations:
            print(f"  - {violation.format()}")
        return 1

    print("[adr-docs] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
