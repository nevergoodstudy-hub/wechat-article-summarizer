# 架构焕新风险看板

> 更新日期：2026-06-09

## 当前阻塞项

| 风险 | 影响 | 当前处置 |
| --- | --- | --- |
| GUI i18n 历史硬编码仍较多 | P3 `i18n 文案抽离完整化` 尚不能验收 | 已加入 `scripts/check_gui_i18n_hardcoded.py` 基线守卫，禁止新增净硬编码；本轮将运行态状态/Toast/日志面板文案迁移到 `tr()`，硬编码基线由 174 收紧到 153，后续继续按页面/对话框逐批降低基线并清理 9 个不可翻译 `tr(...)` |
| DoD 中 GUI 运行态稳定性仍需人工/截图验收 | Phase A 尚不能完全勾选 | 保留自动组合测试证据，后续补 GUI smoke 或截图验证 |
| DoD 中核心功能回归与 MCP 安全基线需要明确验收命令 | Phase A 尚不能完全勾选 | 本轮继续保留质量门禁与安全 smoke，后续补验收矩阵 |

## 回滚点

| 变更类别 | 回滚方式 |
| --- | --- |
| CLI JSON 输出调整 | 回退 `src/wechat_summarizer/presentation/cli/app.py` 与 `tests/test_cli.py` 中本轮 JSON 输出改动 |
| pytest marker 分层守卫 | 回退 `pyproject.toml` marker、`tests/conftest.py` collection policy、`scripts/check_pytest_markers.py` 与对应测试 |
| ADR 文档化 | 回退 `docs/adr/`、`scripts/check_adr_docs.py` 与对应测试 |
| GUI i18n 基线守卫与运行态文案抽离 | 回退 `scripts/check_gui_i18n_hardcoded.py`、`tests/test_gui_i18n_hardcoded_guard.py`、`app_actions.py`、`app_navigation.py`、`runtime_export.py`、`pages/settings_page.py`、`widgets/log_panel.py` 与 `translations/en.json` 中本轮改动 |

## 覆盖率与门禁

| 门禁 | 当前目标 |
| --- | --- |
| lint | `scripts/quality_gate.py --mode lint` 必须通过 |
| architecture | domain/http/i18n/ADR/pytest marker/CI matrix/mypy strictness 守卫必须通过 |
| mypy | `src/wechat_summarizer` 全包必须通过 |
| test | 默认测试套件通过，integration/e2e 由环境变量显式启用 |
