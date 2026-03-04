---
name: type-safety-enforcer
description: "Enforce static type checking across the codebase with mypy. Use this skill to fix P2-3~P2-5 (type errors in progress.py, summary_evaluator.py, secure_storage.py, structured_logging.py), P2-7 (add mypy configuration), and P3-1 (type check config). Configures mypy strict mode, fixes all known type errors, and adds type checking to the dev workflow."
---

# Type Safety Enforcer — P2-3~P2-5, P2-7, P3-1 Fix

Configure mypy strict mode and fix all known type errors across the codebase.

## Audit Reference
- Issues: DEEP_AUDIT_ISSUES.md → P2-3, P2-4, P2-5, P2-7, P3-1
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P2-3~P2-5, P2-7

## Step-by-Step Execution

### Step 1: Add mypy configuration to pyproject.toml
```toml
[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
check_untyped_defs = false

[[tool.mypy.overrides]]
module = [
    "customtkinter.*",
    "click.*",
    "httpx.*",
]
ignore_missing_imports = true
```

### Step 2: Fix BUG-003 — Missing Optional import in progress.py
File: `src/wechat_summarizer/shared/progress.py`
```python
# Since project uses `from __future__ import annotations`:
# Replace Optional[X] with X | None at lines 269, 302, 325
# OR add: from typing import Optional
```

### Step 3: Fix BUG-004 — Type mismatch in summary_evaluator.py
File: `src/wechat_summarizer/domain/services/summary_evaluator.py` line 471
```python
# Add null check for self._summarizer
if self._summarizer is None:
    return result
# Fix argument type: wrap str in ArticleContent if needed
```

### Step 4: Fix BUG-005 — Return type in secure_storage.py
File: `src/wechat_summarizer/shared/secure_storage.py` line 196
```python
# Add explicit str() cast on return value
return str(result)  # instead of returning Any
```

### Step 5: Fix BUG-006 — Type mismatches in structured_logging.py
File: `src/wechat_summarizer/shared/utils/structured_logging.py` lines 52, 87, 134
```python
# Fix return type annotations or add explicit casts
```

### Step 6: Run mypy and fix remaining critical errors
```powershell
# First pass — see what breaks
mypy src/wechat_summarizer/ --ignore-missing-imports 2>&1 | Out-File mypy_report.txt

# Fix errors in priority order:
# 1. Missing return types
# 2. Incompatible types in assignment
# 3. Missing type annotations on function parameters
# 4. Attribute access on Optional without None check
```

### Step 7: Add to pyproject.toml dev deps
```toml
[project.optional-dependencies]
dev = [
    "mypy>=1.13",
    "types-requests",
]
```

## Validation
1. `mypy src/wechat_summarizer/ --ignore-missing-imports` exits with 0 errors (or only third-party stub warnings)
2. BUG-003 through BUG-006 are all resolved
3. `python -c "from wechat_summarizer.shared.progress import *"` works without ImportError
4. All existing tests still pass
