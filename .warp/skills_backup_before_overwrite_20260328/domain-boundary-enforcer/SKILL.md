---
name: domain-boundary-enforcer
description: "Detect and fix hexagonal architecture boundary violations in the domain layer. Use this skill to fix P1-1: find all imports in domain/ that reference infrastructure/, presentation/, or mcp/ packages, replace them with Protocol-based port interfaces, and set up an automated boundary check script."
---

# Domain Layer Boundary Enforcer — P1-1 Fix

The domain layer must not import from infrastructure, presentation, or mcp layers. This skill detects violations and replaces them with proper port interfaces.

## Audit Reference
- Issue: DEEP_AUDIT_ISSUES.md → P1-1
- Research: research_round1_architecture.md → Section 1

## Step-by-Step Execution

### Step 1: Detect all violations
```powershell
grep -rn "from.*infrastructure\|from.*presentation\|from.*mcp\|import.*infrastructure\|import.*presentation\|import.*mcp" src/wechat_summarizer/domain/
```

### Step 2: For each violation, apply the fix pattern

**Pattern: Replace concrete import with Protocol port**
```python
# BEFORE (violation in domain layer):
from wechat_summarizer.infrastructure.adapters.summarizers.openai import OpenAISummarizer

# AFTER (domain defines an interface):
# In domain/ports/summarizer_port.py:
from typing import Protocol

class SummarizerPort(Protocol):
    async def summarize(self, content: str, style: str) -> str: ...

# Domain code uses the Protocol type, not the concrete class
```

### Step 3: Move port definitions to correct location
Port interfaces should live in:
- `src/wechat_summarizer/domain/ports/` — for domain-driven secondary ports
- `src/wechat_summarizer/application/ports/` — for infrastructure secondary ports

### Step 4: Create boundary check script
Create `scripts/check_domain_boundary.py`:
```python
#!/usr/bin/env python3
"""Verify domain layer has no forbidden imports."""
import ast, sys, pathlib

DOMAIN_DIR = pathlib.Path("src/wechat_summarizer/domain")
FORBIDDEN_PREFIXES = ["wechat_summarizer.infrastructure",
                       "wechat_summarizer.presentation",
                       "wechat_summarizer.mcp"]
violations = []

for py_file in DOMAIN_DIR.rglob("*.py"):
    tree = ast.parse(py_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", "") or ""
            for alias in getattr(node, "names", []):
                full = f"{module}.{alias.name}" if module else alias.name
                if any(full.startswith(p) for p in FORBIDDEN_PREFIXES):
                    violations.append(f"{py_file}:{node.lineno}: {full}")

if violations:
    print("Domain boundary violations found:")
    for v in violations:
        print(f"  {v}")
    sys.exit(1)
print("No domain boundary violations found.")
```

## Validation
1. `grep -rn "from.*infrastructure\|from.*presentation\|from.*mcp" src/wechat_summarizer/domain/` returns EMPTY
2. `python scripts/check_domain_boundary.py` exits with code 0
3. All existing tests still pass
4. Port interfaces are properly defined in domain/ports/ or application/ports/
