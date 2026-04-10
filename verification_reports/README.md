# Verification Reports 目录说明

本目录用于保存“可再生的验证产物”，不放核心源码与长期设计文档。

## 分层约定

- `tooling/`：静态检查与工具链输出
  - `ruff` / `mypy` / 格式化日志
- `tests/`：测试执行日志与结果快照
  - `pytest.log` / `pytest_full.log`
- `security/`：安全扫描与渗透检查结果（预留）
- 根目录仅保留“阶段性总览”文档
  - `full_verification.json`
  - `release_*.md`

## 命名建议

- 工具日志：`<tool>_<scope>.log`，如 `ruff_check.log`
- 测试日志：`pytest_<scope>.log`，如 `pytest_full.log`
- 安全报告：`security_<date>_<scope>.md|json`

## 维护规则

1. 一次性验证文件应优先放入对应子目录，而不是根目录。
2. 产物可覆盖更新，不要求长期保留全部历史。
3. 若某报告需长期引用，应迁移到 `docs/audits/` 并在 `docs/README.md` 建入口。
