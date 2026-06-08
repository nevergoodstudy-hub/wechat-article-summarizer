"""ADR documentation guard tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_adr_docs_module() -> ModuleType:
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "check_adr_docs.py"
    spec = importlib.util.spec_from_file_location("check_adr_docs", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("Failed to load ADR guard module")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_current_adr_docs_are_indexed_and_well_formed() -> None:
    """Current ADR files must follow the accepted lightweight template."""
    adr_docs = _load_adr_docs_module()

    assert adr_docs.check_adr_docs() == []


def test_adr_guard_reports_missing_required_section(tmp_path: Path) -> None:
    """ADR files missing trade-off data should fail the guard."""
    adr_docs = _load_adr_docs_module()
    adr_dir = tmp_path / "adr"
    adr_dir.mkdir()
    (adr_dir / "README.md").write_text(
        "[ADR-001](001-test-decision.md)\n",
        encoding="utf-8",
    )
    (adr_dir / "001-test-decision.md").write_text(
        "# ADR-001: Test Decision\n"
        "\n"
        "## Status\n"
        "Accepted\n"
        "\n"
        "## Context\n"
        "Problem.\n"
        "\n"
        "## Decision\n"
        "Decision.\n",
        encoding="utf-8",
    )

    violations = adr_docs.check_adr_docs(adr_dir)

    assert {violation.message for violation in violations} >= {
        "missing required section: ## Rationale",
        "missing required section: ## Trade-offs",
        "missing required section: ## Consequences",
    }


def test_adr_guard_reports_missing_index_entry(tmp_path: Path) -> None:
    """Every ADR file should be linked from the index."""
    adr_docs = _load_adr_docs_module()
    adr_dir = tmp_path / "adr"
    adr_dir.mkdir()
    (adr_dir / "README.md").write_text("# Architecture Decision Records\n", encoding="utf-8")
    (adr_dir / "001-test-decision.md").write_text(
        "# ADR-001: Test Decision\n"
        "\n"
        "## Status\n"
        "Accepted\n"
        "\n"
        "## Context\n"
        "Problem.\n"
        "\n"
        "## Decision\n"
        "Decision.\n"
        "\n"
        "## Rationale\n"
        "Rationale.\n"
        "\n"
        "## Trade-offs\n"
        "Trade-off.\n"
        "\n"
        "## Consequences\n"
        "- Positive: good.\n",
        encoding="utf-8",
    )

    violations = adr_docs.check_adr_docs(adr_dir)

    assert len(violations) == 1
    assert "ADR index missing entry for 001-test-decision.md" in violations[0].message
