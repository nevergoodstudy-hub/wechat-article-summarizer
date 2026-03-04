---
name: test-generator
description: "Generate unit tests for uncovered modules in the WeChat Article Summarizer project. Use this skill to create pytest-based unit tests for scrapers, CLI, SimpleSummarizer, observability, and async_executor modules. Tests should use mocks to isolate external dependencies."
---

# Test Generator Agent

Generate missing unit tests for the WeChat Article Summarizer project.

## Project Context
- Python 3.10+, DDD + Hexagonal Architecture
- Test framework: pytest + pytest-asyncio + pytest-mock
- Test dir: `tests/`
- Source: `src/wechat_summarizer/`
- Config: `pyproject.toml` with markers: unit, integration, slow
- Existing fixtures in `tests/conftest.py`: sample_article, sample_content, sample_wechat_url, mock_scraper, mock_summarizer, wechat_html_response, minimal_container

## Modules Needing Tests

### 1. SimpleSummarizer (`tests/test_simple_summarizer.py`)
- Source: `src/wechat_summarizer/infrastructure/adapters/summarizers/simple.py`
- Test: summarize() with concise and bullet_points styles, _extract_tags, _extract_key_points
- Use `sample_content` fixture from conftest.py
- No external deps needed

### 2. Scrapers (`tests/test_scrapers.py`)
- Source files: `src/wechat_summarizer/infrastructure/adapters/scrapers/`
  - `generic_httpx.py` (GenericHttpxScraper)
  - `wechat_httpx.py` (WechatHttpxScraper)
  - `zhihu.py` (ZhihuScraper)
  - `toutiao.py` (ToutiaoScraper)
- Test approach: Mock httpx.Client responses using `respx` or `unittest.mock.patch`
- Test: can_handle() URL matching, scrape() with mocked HTML responses, error handling (timeout, 403, 404)
- Use `wechat_html_response` fixture for WechatHttpxScraper

### 3. CLI Commands (`tests/test_cli.py`)
- Source: `src/wechat_summarizer/presentation/cli/app.py`
- Test using Click's `CliRunner`
- Test: `cli --version`, `cli --help`, `fetch` with mocked container
- Mock `get_container()` to avoid real service connections

### 4. Observability Metrics (`tests/test_observability.py`)
- Source: `src/wechat_summarizer/infrastructure/observability/metrics.py`
- Test: MetricsCollector singleton, record_fetch, record_summary, memory fallback counters
- No external deps needed (test the fallback mode without opentelemetry)

## Test Writing Rules
- Mark all tests with `@pytest.mark.unit`
- Use `from __future__ import annotations`
- Use pytest fixtures from conftest.py where applicable
- Mock all external HTTP calls (never make real network requests)
- Each test file should be self-contained with clear docstrings
- Use `tmp_path` fixture for any file I/O
- Do NOT commit changes
- Run `python -m pytest tests/test_simple_summarizer.py tests/test_scrapers.py tests/test_cli.py tests/test_observability.py -v --tb=short` to verify tests pass
