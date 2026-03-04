---
name: code-quality
description: "Improve code quality in the WeChat Article Summarizer project. Use this skill for automated code style fixes (ruff), test infrastructure improvements, and pytest-timeout setup. Targets WARN-001 (4711 ruff issues) and WARN-004 (test suite structural defects) from TEST_ISSUES.txt."
---

# Code Quality Agent

Fix code quality issues in the WeChat Article Summarizer project.

## Project Context
- Python 3.10+ project, source in `src/wechat_summarizer/`
- Tests in `tests/`
- Config: `pyproject.toml` (ruff, mypy, pytest settings)
- Ruff rules: E, F, I, N, W, UP (line 165 of pyproject.toml)

## Issues

### WARN-001: 4711 Ruff code style issues (83% auto-fixable)
- Run `ruff check src --fix` to auto-fix ~3913 issues
- Categories: UP035/UP037/UP042/UP045 (type annotation modernization), I001/I002 (import sorting), F401 (unused imports), W293/W291 (whitespace), E722 (bare except)
- After auto-fix, run `ruff check src` to assess remaining manual-fix issues
- Focus on fixing the most impactful remaining issues: F401 (unused imports), E722 (bare except → specific exceptions)

### WARN-004: Test suite structural defects
- 387 tests total, only 201 (52%) can run independently
- Problem: Tests depend on Container which connects to external services
- Fix:
  1. Add `pytest-timeout` to dev dependencies in `pyproject.toml`
  2. Add `timeout = 30` to `[tool.pytest.ini_options]`
  3. Create/update `tests/conftest.py` with environment-aware fixtures that auto-skip tests requiring external services
  4. Add a mock Container fixture that doesn't connect to external services

## Execution Steps
1. Run `ruff check src --fix` for auto-fixes
2. Run `ruff check src` to assess remaining issues
3. Update `pyproject.toml` with pytest-timeout
4. Review and improve `tests/conftest.py`
5. Report changes and remaining issues
