# 仓库整理周期（第 6 轮落地）

本计划用于把“文件整理”变成可持续机制，而不是一次性动作。

## 周期节奏

### 每周（15~30 分钟）

- 检查根目录是否出现新增临时文件（log/tmp/report）。
- 检查 `verification_reports/` 是否按 `tooling/tests/security` 分层。
- 检查 `docs/` 新增文档是否在 `docs/README.md` 建立入口。

### 每月（30~60 分钟）

- 复核 `.gitignore` 是否覆盖新增构建缓存目录。
- 抽查 `apps/`、`services/` 是否有运行产物误入版本控制。
- 将阶段性报告从根目录下沉到 `docs/audits/` 或 `verification_reports/`。

### 每版本发布前

- 运行一次结构体检：
  1. 根目录白名单校验（参见 `docs/PROJECT_STRUCTURE.md`）
  2. 文档入口一致性校验（`README.md` / `docs/README.md` / `docs/MIGRATION_INDEX.md`）
  3. 验证报告目录整洁性校验

## 命名规范（增量约束）

- 计划文档：`docs/plans/<TOPIC>_PLAN.md`
- 审计文档：`docs/audits/<TOPIC>_AUDIT.md`
- 验证日志：`verification_reports/<group>/<tool>_<scope>.log`

## 触发“额外整理轮次”的条件

满足任一条件即建议启动额外一轮整理：

1. 根目录新增 5 个以上非白名单文件。
2. 任一子目录出现 >2000 个新增构建产物被纳入跟踪。
3. 文档入口断链（README 指向不存在文件）。
4. 新增顶层目录但无职责说明。
