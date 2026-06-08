# 架构焕新风险看板

> 更新日期：2026-06-09

## 当前阻塞项

| 风险 | 影响 | 当前处置 |
| --- | --- | --- |
| GUI i18n 历史硬编码仍较多 | P3 `i18n 文案抽离完整化` 尚不能验收 | 已加入 `scripts/check_gui_i18n_hardcoded.py` 基线守卫，禁止新增净硬编码；本轮补充重复翻译键检查，迁移首页 dashboard/状态卡、快捷键描述、API 密钥状态、低内存提示、sidebar/splash、退出确认、批量压缩导出与 Word 预览文案，硬编码基线由 174 分阶段收紧到 101，不可翻译 `tr(...)` 由 9 清零到 0；后续继续迁移 demo/通用模型/剩余对话框硬编码 |
| DoD 中 GUI 运行态稳定性仍需人工/截图验收 | Phase A 尚不能完全勾选 | 保留自动组合测试证据，后续补 GUI smoke 或截图验证 |
| DoD 中核心功能回归与 MCP 安全基线需要明确验收命令 | Phase A 尚不能完全勾选 | 本轮继续保留质量门禁与安全 smoke，后续补验收矩阵 |

## 回滚点

| 变更类别 | 回滚方式 |
| --- | --- |
| CLI JSON 输出调整 | 回退 `src/wechat_summarizer/presentation/cli/app.py` 与 `tests/test_cli.py` 中本轮 JSON 输出改动 |
| pytest marker 分层守卫 | 回退 `pyproject.toml` marker、`tests/conftest.py` collection policy、`scripts/check_pytest_markers.py` 与对应测试 |
| ADR 文档化 | 回退 `docs/adr/`、`scripts/check_adr_docs.py` 与对应测试 |
| GUI i18n 基线守卫与产品文案抽离 | 回退 `scripts/check_gui_i18n_hardcoded.py`、`tests/test_gui_i18n_hardcoded_guard.py`、`app_layout.py`、`app_actions.py`、`app_navigation.py`、`runtime_export.py`、`runtime_optimizations.py`、`settings_api_actions.py`、`pages/settings_page.py`、`frames/home_dashboard.py`、`frames/home_info.py`、`frames/history.py`、`frames/single_clipboard.py`、`dialogs/batch_archive_export.py`、`dialogs/exit_confirm.py`、`dialogs/word_preview_batch.py`、`dialogs/word_preview_render.py`、`dialogs/word_preview_single.py`、`widgets/log_panel.py`、`widgets/sidebar.py`、`widgets/splash_screen.py` 与 `translations/en.json` 中本轮改动 |

## 覆盖率与门禁

| 门禁 | 当前目标 |
| --- | --- |
| lint | `scripts/quality_gate.py --mode lint` 必须通过 |
| architecture | domain/http/i18n/ADR/pytest marker/CI matrix/mypy strictness 守卫必须通过 |
| mypy | `src/wechat_summarizer` 全包必须通过 |
| test | 默认测试套件通过，integration/e2e 由环境变量显式启用 |
