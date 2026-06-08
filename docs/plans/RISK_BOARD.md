# 架构焕新风险看板

> 更新日期：2026-06-09

## 当前阻塞项

| 风险 | 影响 | 当前处置 |
| --- | --- | --- |
| 无 | 当前没有阻塞项 | 本地全量质量门禁通过；GitHub PR #3 合并状态为 `CLEAN`，线上检查均为成功或预期跳过 |

## 已关闭风险

| 风险 | 关闭证据 |
| --- | --- |
| 线上 PR 检查曾处于运行中 | 2026-06-09 复核 `gh pr view 3 --json mergeStateStatus,statusCheckRollup`：PR #3 合并状态为 `CLEAN`；Lint、Code Quality、Security Audit、Docs Build、Build Package、Python 3.11~3.14 测试矩阵均完成且成功；Build Windows Executable、Build Python Package、Publish to PyPI 为工作流条件下的预期跳过 |
| GUI i18n 历史硬编码仍较多 | `scripts/check_gui_i18n_hardcoded.py` 已扩展并接入架构门禁，覆盖标题、Toast、状态、live-region announce、用户可见关键字和 f-string；当前硬编码基线由 174 分阶段收紧到 0，不可翻译 `tr(...)` 由 9 清零到 0；GUI/i18n 专项 101 个用例通过 |
| DoD 中 GUI 运行态稳定性仍需人工/截图验收 | `scripts/quality_gate.py --mode phase-a` 已加入 GUI 稳定验收组，覆盖 `tests/test_gui_app_composition.py` 与 `tests/test_gui_i18n_hardcoded_guard.py`，当前 77 个用例通过，验证薄入口依赖注入、GUI 组合拆分、单文件 <400 行目标与 i18n 0/0 守卫 |
| DoD 中核心功能回归与 MCP 安全基线需要明确验收命令 | `scripts/quality_gate.py --mode phase-a` 已加入核心回归组与 MCP 安全组，当前核心 37 个用例通过、MCP 安全 135 个用例通过，并已纳入默认 `quality_gate.py --mode all` |

## 回滚点

| 变更类别 | 回滚方式 |
| --- | --- |
| CLI JSON 输出调整 | 回退 `src/wechat_summarizer/presentation/cli/app.py` 与 `tests/test_cli.py` 中本轮 JSON 输出改动 |
| pytest marker 分层守卫 | 回退 `pyproject.toml` marker、`tests/conftest.py` collection policy、`scripts/check_pytest_markers.py` 与对应测试 |
| ADR 文档化 | 回退 `docs/adr/`、`scripts/check_adr_docs.py` 与对应测试 |
| GUI i18n 基线守卫与产品文案抽离 | 回退 `scripts/check_gui_i18n_hardcoded.py`、`tests/test_gui_i18n_hardcoded_guard.py`、`app_layout.py`、`app_actions.py`、`app_navigation.py`、`runtime_batch.py`、`runtime_export.py`、`runtime_optimizations.py`、`settings_api_actions.py`、`pages/settings_page.py`、`frames/home_dashboard.py`、`frames/home_info.py`、`frames/history.py`、`frames/single_article.py`、`frames/single_clipboard.py`、`frames/batch_processing.py`、`frames/settings_language_actions.py`、`dialogs/batch_archive_export.py`、`dialogs/exit_confirm.py`、`dialogs/export_dialogs.py`、`dialogs/settings_dialogs.py`、`dialogs/word_preview_batch.py`、`dialogs/word_preview_render.py`、`dialogs/word_preview_single.py`、`dialogs/word_preview_window.py`、`components/contextmenu_demo.py`、`components/datagrid_demo.py`、`components/datagrid_toolbar.py`、`components/graph_viewer.py`、`components/select_dropdown.py`、`components/sidebar_demo.py`、`components/virtuallist_demo.py`、`utils/accessibility_demo.py`、`utils/animation_demo.py`、`utils/autosave_demo.py`、`utils/autosave_dialog.py`、`utils/clipboard_auto.py`、`utils/lazy_demo.py`、`utils/microinteractions_demo.py`、`utils/performance_demo.py`、`utils/performance_overlay.py`、`utils/responsive_demo.py`、`utils/shortcuts_demo.py`、`utils/shortcuts_models.py`、`utils/shortcuts_panel.py`、`utils/transition_demo.py`、`viewmodels/batch_process_viewmodel.py`、`viewmodels/single_process_viewmodel.py`、`widgets/log_panel.py`、`widgets/sidebar.py`、`widgets/splash_screen.py`、`widgets/toast_notification.py` 与 `translations/en.json` 中本轮改动 |

## 覆盖率与门禁

| 门禁 | 当前目标 |
| --- | --- |
| lint | `scripts/quality_gate.py --mode lint` 必须通过 |
| architecture | domain/http/i18n/ADR/pytest marker/CI matrix/mypy strictness 守卫必须通过 |
| mypy | `src/wechat_summarizer` 全包必须通过 |
| test | 默认测试套件通过，integration/e2e 由环境变量显式启用 |
