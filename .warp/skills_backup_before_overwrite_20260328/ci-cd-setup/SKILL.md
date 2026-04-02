---
name: ci-cd-setup
description: "Set up a complete CI/CD pipeline using GitHub Actions. Use this skill to fix P2-8: create workflows for linting (ruff), type checking (mypy), testing (pytest with timeout), security scanning (pip-audit), and build verification. Includes dependency caching and matrix testing for Python 3.12-3.14."
---

# CI/CD Pipeline Setup — P2-8 Fix

Create a GitHub Actions CI/CD pipeline with lint → typecheck → test → security scan stages.

## Audit Reference
- Issue: DEEP_AUDIT_ISSUES.md → P2-8
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P2-8

## Files to Create

### 1. `.github/workflows/ci.yml`
```yaml
name: CI
on:
  push:
    branches: [master, main, develop]
  pull_request:
    branches: [master, main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install linting tools
        run: pip install ruff
      - name: Ruff check
        run: ruff check src/ tests/
      - name: Ruff format check
        run: ruff format --check src/ tests/

  typecheck:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          cache: 'pip'
      - name: Install deps
        run: pip install -e ".[dev]" mypy
      - name: mypy
        run: mypy src/wechat_summarizer/ --ignore-missing-imports

  test:
    runs-on: ${{ matrix.os }}
    needs: lint
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
        python-version: ['3.12', '3.13', '3.14']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      - name: Install deps
        run: pip install -e ".[dev]"
      - name: Run tests
        run: pytest tests/ --timeout=60 -x --tb=short -q

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Install deps
        run: pip install -e "." pip-audit
      - name: Audit dependencies
        run: pip-audit
```

### 2. Pre-commit config `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### 3. Update `pyproject.toml` dev dependencies
Add to `[project.optional-dependencies]`:
```toml
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-timeout>=2.3",
    "pytest-randomly>=3.15",
    "pytest-xdist>=3.5",
    "pytest-mock>=3.14",
    "mypy>=1.13",
    "ruff>=0.9",
    "pip-audit>=2.7",
    "pre-commit>=4.0",
]
```

## Validation
1. `gh workflow run ci.yml` or push to trigger CI
2. All 4 jobs (lint, typecheck, test, security) pass
3. Matrix testing covers Python 3.12-3.14 on Linux + Windows
4. Security scan reports no high-severity vulnerabilities
