# v2.4.3 — 模块化重构与稳定性发布 / Modular Refactor & Stability Release

- 发布日期 / Release date: 2026-04-13
- Git 标签 / Git tag: `v2.4.3`
- 发布分支 / Release branch: `chore/cleanup-legacy-docs`
- 兼容性 / Compatibility: Python `>=3.10,<3.15`

## 中文说明

### 版本亮点

- 完成 MCP 薄组合根重构，注册逻辑按 `toolsets` 与 `resources` 拆分，降低入口复杂度。
- 新增 `features/article_workflow` 垂直切片服务，用统一编排替代零散流程调用。
- 将依赖注入装配提取到 `infrastructure/config/assembly.py`，统一构建抓取器、摘要器、导出器、向量组件与存储。
- GUI 主入口完成壳层瘦身，`app.py` 进一步拆分为 `app_bootstrap.py`、`app_navigation.py`、`app_actions.py`、`app_runtime.py`。
- 新增 GUI 组合测试、MCP 组合测试、入口冒烟测试、质量门禁测试与结构化日志回归测试。

### 修复内容

- 修复 `reload_summarizers()` 之后的缓存失效链路，确保摘要器热重载后依赖对象同步刷新。
- 修复 Python 3.14 环境中 `pydantic` / `pydantic-core` 版本不匹配导致的 CLI、MCP 与测试失败问题。
- 修复 URL 校验、SSRF 防护、向量存储装配与 CLI 导出等回归问题，恢复主要入口的可运行状态。

### 验证结果

- `python -m ruff check src tests`
- `python -m mypy src\wechat_summarizer --ignore-missing-imports`
- `python -m pytest tests -q --no-cov`：`695 passed, 20 skipped`
- `python -m wechat_summarizer --help`
- `python -m wechat_summarizer.mcp --help`

### 发行资产

- `wechat_summarizer-2.4.3.tar.gz`
- `wechat_summarizer-2.4.3-py3-none-any.whl`

## English

### Highlights

- Refactored MCP into a thin composition root with dedicated `toolsets` and `resources`.
- Added the `features/article_workflow` vertical slice to centralize article fetch, summarize, and export orchestration.
- Extracted dependency wiring into `infrastructure/config/assembly.py` to modularize scrapers, summarizers, exporters, vector components, and storage.
- Reduced GUI shell complexity by splitting the main app entry into `app_bootstrap.py`, `app_navigation.py`, `app_actions.py`, and `app_runtime.py`.
- Added GUI composition coverage, MCP composition coverage, entrypoint smoke tests, quality gate tests, and structured logging regression coverage.

### Fixes

- Fixed summarizer reload cache invalidation so dependent services and use cases refresh correctly after reloading summarizers.
- Repaired the Python 3.14 environment by aligning `pydantic` and `pydantic-core`, restoring runnable CLI, MCP, and test entrypoints.
- Resolved regressions around URL validation, SSRF protection, vector-store wiring, and CLI export flow.

### Verification

- `python -m ruff check src tests`
- `python -m mypy src\wechat_summarizer --ignore-missing-imports`
- `python -m pytest tests -q --no-cov`: `695 passed, 20 skipped`
- `python -m wechat_summarizer --help`
- `python -m wechat_summarizer.mcp --help`

### Release Assets

- `wechat_summarizer-2.4.3.tar.gz`
- `wechat_summarizer-2.4.3-py3-none-any.whl`
