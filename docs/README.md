# Docs 导航索引

本目录用于存放长期维护的项目文档。建议按“主题分层 + 单一入口”使用。

## 目录结构

- `ARCHITECTURE.md`：系统架构总览
- `GETTING_STARTED.md`：新手上手
- `CONTRIBUTING.md`：贡献流程
- `ITERATION_ROADMAP.md`：迭代路线
- `WINDOWS_BUILD.md`：Windows 构建说明
- `GUI_REFACTORING.md` / `GUI_Animation_Optimization.md`：GUI 专题
- `MIGRATION_INDEX.md`：历史文档迁移说明
- `PROJECT_STRUCTURE.md`：仓库目录边界与治理约定

### 子目录

- `audits/`：审计与问题清单
  - `SECURITY_AUDIT.md`
  - `DEEP_AUDIT_ISSUES.md`
  - `DEEP_AUDIT_IMPROVEMENTS.md`
  - `TEST_REPORT.md`
  - `TEST_ISSUES.txt`
- `plans/`：规划与改造方案
  - `IMPROVEMENT_PLAN.md`
  - `ARCHITECTURE_RENOVATION_PLAN.md`
  - `ARCHITECTURE_RENEWAL_CHECKLIST.md`
  - `REPO_HYGIENE_CYCLE.md`
  - `DEEP_RENEWAL_FEASIBILITY_PLAN.md`
  - `CORE_SCOPE_VIEW.md`
- `api/`：API 相关文档
- `new_stack_program/`：新技术栈方案材料
- `project_focused/`：项目聚焦类文档

## 维护约定

1. 新文档优先放入 `docs/`，避免回流到仓库根目录。
2. “计划类/审计类”必须分别放在 `docs/plans/`、`docs/audits/`。
3. 新增文档后需同步更新：
   - 根 `README.md` 的文档入口
   - `docs/MIGRATION_INDEX.md`（若涉及迁移或替代）
4. 临时输出（日志、一次性报告）不放在 `docs/`，统一放 `verification_reports/`。
