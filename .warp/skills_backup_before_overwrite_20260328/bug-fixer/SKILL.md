---
name: bug-fixer
description: "Fix known bugs in the WeChat Article Summarizer project. Use this skill when investigating and fixing code bugs including: deprecated API usage, missing imports, type errors, null safety issues, and container initialization problems. Targets BUG-001 through BUG-006 from the project's TEST_ISSUES.txt."
---

# Bug Fixer Agent

Fix the known bugs documented in TEST_ISSUES.txt for the WeChat Article Summarizer (wechat-summarizer) v2.4.0 project.

## Project Context
- Python 3.10+ project using DDD + Hexagonal Architecture
- Source code in `src/wechat_summarizer/`
- Uses `from __future__ import annotations` for deferred type evaluation

## Bug List and Fix Instructions

### BUG-001 (P0): Container initialization blocks test suite
- File: `src/wechat_summarizer/infrastructure/config/container.py`
- Problem: `_create_summarizers()` tries connecting to external services (Ollama at localhost:11434), loading large models (sentence-transformers), causing test suite hangs >4 minutes.
- Fix approach:
  1. Add a `create_minimal()` classmethod to Container that creates an instance without connecting to external services
  2. Add timeout (3s) for service availability checks in `_create_base_summarizers()`
  3. Update `tests/conftest.py` to provide a mock/minimal Container fixture

### BUG-002 (P2): Deprecated datetime.utcnow()
- File: `src/wechat_summarizer/infrastructure/adapters/exporters/onenote.py` line 464
- Problem: `datetime.utcnow()` is deprecated in Python 3.12+
- Fix: Replace `datetime.utcnow().isoformat()` with `datetime.now(datetime.UTC).isoformat()`
- Ensure `datetime` is imported from the `datetime` module correctly

### BUG-003 (P2): Missing Optional import in progress.py
- File: `src/wechat_summarizer/shared/progress.py` lines 269, 302, 325
- Problem: Uses `Optional[...]` type annotations but never imports `Optional` from `typing`
- Fix: Since file uses `from __future__ import annotations`, replace `Optional[X]` with `X | None` (modern Python 3.10+ syntax) at all occurrences

### BUG-004 (P2): Null safety and type mismatch in summary_evaluator.py
- File: `src/wechat_summarizer/domain/services/summary_evaluator.py` line 471
- Problem: `self._summarizer` could be None, and `summarize()` expects `ArticleContent` but receives `str`
- Fix:
  1. Add null check: `if self._summarizer is None: return result`
  2. Wrap the prompt string properly for the summarizer's expected input type

### BUG-005 (P3): Return type Any instead of str in secure_storage.py
- File: `src/wechat_summarizer/shared/secure_storage.py` line 196
- Problem: Function returns Any but declares return type str
- Fix: Add explicit `str()` cast on the return value

### BUG-006 (P3): Type mismatches in structured_logging.py
- File: `src/wechat_summarizer/shared/utils/structured_logging.py` lines 52, 87, 134
- Problem: Multiple return type mismatches
- Fix: Correct type annotations or add explicit type casts

## Execution Steps
1. Read each affected file
2. Apply the fix for each bug
3. Verify fixes compile correctly (no syntax errors)
4. Report what was changed
