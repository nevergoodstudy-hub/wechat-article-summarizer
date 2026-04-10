---
name: container-lazy-init
description: "Refactor the DI container from eager to lazy initialization to unblock 186 tests. Use this skill to fix P0-1: convert container.py to use cached_property/lazy providers, create a test container with mock adapters in conftest.py, and eliminate module-level container instantiation across the codebase."
---

# Container Lazy Initialization — P0-1 Fix

Refactor the DI container so that external services (LLM APIs, httpx pools, storage) are only instantiated on first access, not at import time. This unblocks 186 tests currently blocked by connection timeouts.

## Audit Reference
- Issue: DEEP_AUDIT_ISSUES.md → P0-1
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P0-1

## Project Context
- Container: `src/wechat_summarizer/infrastructure/config/container.py`
- Settings: `src/wechat_summarizer/infrastructure/config/settings.py`
- Tests: `tests/` (387 total, 186 blocked)
- Test config: `tests/conftest.py`

## Step-by-Step Execution

### Step 1: Analyze current container
1. Read `src/wechat_summarizer/infrastructure/config/container.py` fully
2. Identify all eagerly-initialized services (look for `__init__` body that creates clients)
3. List all external dependencies that connect at init time (httpx, LLM clients, sentence-transformers, Ollama)

### Step 2: Refactor to lazy initialization
Convert each eager service creation to a `@cached_property` pattern:

```python
from functools import cached_property

class Container:
    def __init__(self, config: Settings):
        self._config = config
        # NO service creation here — only store config

    @cached_property
    def llm_client(self) -> LLMPort:
        # Created only on first access
        return self._build_llm_client()

    @cached_property
    def scraper(self) -> ScraperPort:
        return HttpxScraperAdapter(timeout=self._config.scraper_timeout)

    def _build_llm_client(self) -> LLMPort:
        provider = self._config.llm_provider
        if provider == "openai":
            return OpenAIAdapter(api_key=self._config.openai_api_key)
        # ... other providers
```

### Step 3: Eliminate module-level container instantiation
Search the entire codebase for module-level container creation:

```powershell
grep -rn "container\s*=\s*Container(" src/
grep -rn "get_container\(\)" src/
```

Replace with lazy accessor pattern:

```python
# Before (BAD):
container = Container()  # runs at import!

# After (GOOD):
_container: Container | None = None

def get_container() -> Container:
    global _container
    if _container is None:
        _container = Container(config=load_settings())
    return _container
```

### Step 4: Create test container fixture
Update `tests/conftest.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture(scope="session")
def test_settings():
    """Minimal settings that don't require external services"""
    return Settings(
        llm_provider="mock",
        scraper_timeout=5,
        # ... minimal test config
    )

@pytest.fixture(scope="session")
def mock_container(test_settings):
    """Container with all external deps mocked"""
    container = Container(config=test_settings)
    # Override cached_properties with mocks
    type(container).llm_client = property(lambda self: AsyncMock(spec=LLMPort))
    type(container).scraper = property(lambda self: AsyncMock(spec=ScraperPort))
    type(container).storage = property(lambda self: MagicMock(spec=StoragePort))
    return container

@pytest.fixture(autouse=True)
def patch_global_container(mock_container, monkeypatch):
    """Ensure all code uses the mock container"""
    monkeypatch.setattr(
        "wechat_summarizer.infrastructure.config.container.get_container",
        lambda: mock_container
    )
```

### Step 5: Verify
1. `pytest tests/ --co` — all 387 tests should be collected with no import errors
2. `pytest tests/ -x --timeout=10` — no test should hang on external connections
3. `pytest tests/ -v --tb=short` — run full suite, expect significant increase in passing tests

## Success Criteria
- Zero external network calls during test collection/execution
- All 387 tests are collectable
- Previously blocked 186 tests now execute (may need individual mock fixes)
- Container initialization time < 100ms in tests

## Key Files to Modify
1. `src/wechat_summarizer/infrastructure/config/container.py` — core refactoring
2. `tests/conftest.py` — test container fixture
3. Any file with module-level `Container()` or `get_container()` calls
4. `src/wechat_summarizer/__main__.py` — entry point container creation
5. `src/wechat_summarizer/presentation/gui/app.py` — GUI entry point
6. `src/wechat_summarizer/presentation/cli/app.py` — CLI entry point
