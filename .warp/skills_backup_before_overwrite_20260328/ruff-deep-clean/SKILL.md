---
name: ruff-deep-clean
description: "Deep clean Python code style issues using ruff. Use this skill for aggressive automated fixes (--unsafe-fixes) and manual fixes for remaining issues like E722 bare-except, F841 unused-variable, F401 unused-import, F821 undefined-name, and E702 multiple-statements. Targets code under src/ directory."
---

# Ruff Deep Clean Agent

Aggressively fix all remaining ruff code style issues in the WeChat Article Summarizer project.

## Current State (736 issues remaining)
- 645 W293 blank-line-with-whitespace
- 26 E402 module-import-not-at-top-of-file
- 13 F841 unused-variable
- 9 N806 non-lowercase-variable-in-function
- 8 UP042 replace-str-enum
- 7 E702 multiple-statements-on-one-line-semicolon
- 6 F401 unused-import
- 6 F821 undefined-name (CRITICAL)
- 5 W291 trailing-whitespace
- 3 UP046 non-pep695-generic-class
- 2 E722 bare-except
- 2 N802 invalid-function-name
- 1 F811 redefined-while-unused
- 1 N803 invalid-argument-name

## Execution Steps

### Step 1: Aggressive auto-fix
Run `ruff check src --fix --unsafe-fixes` to fix whitespace and other auto-fixable issues.

### Step 2: Fix F821 (undefined-name) - CRITICAL
These cause runtime errors. Read each file, find the undefined names, and add proper imports or fix references.
Run `ruff check src --select F821` to find them.

### Step 3: Fix F401 (unused-import)
Remove unused imports. Run `ruff check src --select F401` to find them.

### Step 4: Fix F841 (unused-variable)
Remove or use unused variables. Run `ruff check src --select F841` to find them.
Common pattern: replace `x = something()` with `_ = something()` if return value is intentionally discarded.

### Step 5: Fix E722 (bare-except)
Replace bare `except:` with specific exceptions like `except Exception:`.
Run `ruff check src --select E722` to find them.

### Step 6: Fix E702 (multiple-statements-on-one-line)
Split semicolon-separated statements into separate lines.
Run `ruff check src --select E702` to find them.

### Step 7: Skip N-series issues
N806/N802/N803 are naming convention issues that may be intentional (e.g., class-like variable names, callback signatures). Skip unless clearly wrong.

### Step 8: Skip E402 issues
E402 (module-import-not-at-top) are often intentional lazy imports inside functions. Skip.

### Step 9: Final verification
Run `ruff check src` to count remaining issues. Target: <50 remaining (only intentional exceptions).

## Rules
- Config: pyproject.toml has `line-length = 100`, `target-version = "py312"`, rules: E, F, I, N, W, UP
- Do NOT modify test files unless they have F821 errors
- Do NOT commit changes
