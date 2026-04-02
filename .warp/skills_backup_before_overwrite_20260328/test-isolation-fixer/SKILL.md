---
name: test-isolation-fixer
description: "Fix the 52% of tests that cannot run independently due to shared state, execution order dependencies, or container coupling. Use this skill to fix P1-8: add pytest-randomly for order detection, refactor shared global state into fixtures, replace file system side effects with tmp_path, and ensure every test passes when run in isolation."
---

# Test Isolation Fixer — P1-8 Fix

Fix test independence so all 387 tests can run in any order, individually or in parallel.

## Audit Reference
- Issue: DEEP_AUDIT_ISSUES.md → P1-8
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P1-8

## Step-by-Step Execution

### Step 1: Install diagnostic tools
```powershell
pip install pytest-randomly pytest-xdist
```

### Step 2: Detect order-dependent tests
```powershell
# Run tests in random order 3 times to find failures
pytest tests/ --randomly-seed=12345 -x --tb=short 2>&1 | Out-File test_random_1.txt
pytest tests/ --randomly-seed=67890 -x --tb=short 2>&1 | Out-File test_random_2.txt
pytest tests/ --randomly-seed=11111 -x --tb=short 2>&1 | Out-File test_random_3.txt
```

### Step 3: Categorize failures
For each failing test, identify the root cause:

**Category A: Shared global state**
- Symptoms: Test passes alone but fails when run after another test
- Fix: Move global state into fixture with proper teardown
```python
# BAD: module-level mutable state
_cache = {}

# GOOD: fixture-scoped state
@pytest.fixture(autouse=True)
def reset_cache():
    _cache.clear()
    yield
    _cache.clear()
```

**Category B: File system side effects**
- Symptoms: Test creates files that interfere with other tests
- Fix: Use `tmp_path` fixture
```python
# BAD:
def test_export():
    with open("output.html", "w") as f:
        f.write(result)

# GOOD:
def test_export(tmp_path):
    output = tmp_path / "output.html"
    output.write_text(result)
```

**Category C: Container singleton coupling**
- Symptoms: Test depends on container state set by another test
- Fix: Use mock_container fixture from container-lazy-init skill
```python
@pytest.fixture
def fresh_container():
    return Container(config=TestSettings())
```

**Category D: Database/storage leaks**
- Symptoms: Test data persists between tests
- Fix: Transaction rollback or fixture cleanup

### Step 4: Fix conftest.py
Ensure `tests/conftest.py` has:
```python
@pytest.fixture(autouse=True)
def isolate_test(tmp_path, monkeypatch):
    """Universal test isolation fixture"""
    # Redirect all file I/O to tmp_path
    monkeypatch.setenv("WECHAT_SUMMARIZER_DATA_DIR", str(tmp_path))
    # Reset any singleton state
    # Clear module-level caches
    yield
```

### Step 5: Add pytest-randomly to project config
In `pyproject.toml`:
```toml
[tool.pytest.ini_options]
addopts = "-p randomly"
markers = [
    "unit: Unit tests (no external deps)",
    "integration: Integration tests (may need external services)",
    "slow: Slow tests (>5s)",
]
```

### Step 6: Add to dev dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest-randomly",
    "pytest-xdist",
    "pytest-timeout",
]
```

## Validation
1. `pytest tests/ --randomly-seed=random -x` passes 3 consecutive times with different seeds
2. `pytest tests/test_specific.py::test_one_test -v` passes for each previously-failing test
3. `pytest tests/ -n auto` (parallel execution) passes
4. No test writes files outside of `tmp_path`
