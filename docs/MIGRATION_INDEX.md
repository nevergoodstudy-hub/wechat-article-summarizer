# 文档迁移索引（清理后保留）

本文件用于说明历史文档清理后的去向，并作为 `docs/` 的轻量导航入口。

## 已清理内容范围

- `docs/` 下旧架构文档与历史 `.docx` 文档
- 仓库根目录下历史方案类 `.docx` 文件

## 目录导航（当前建议入口）

### 1) 快速上手与协作

- 项目总览：`README.md`
- 快速开始：`docs/GETTING_STARTED.md`
- 贡献指南：`docs/CONTRIBUTING.md`
- 变更记录：`CHANGELOG.md`

### 2) 架构与迭代

- 架构总览：`docs/ARCHITECTURE.md`
- 迭代路线图：`docs/ITERATION_ROADMAP.md`
- 架构重整计划：`docs/plans/ARCHITECTURE_RENOVATION_PLAN.md`
- 改进计划：`docs/plans/IMPROVEMENT_PLAN.md`

### 3) 安全与审计

- 安全说明：`SECURITY.md`
- 安全审计：`docs/audits/SECURITY_AUDIT.md`
- 深度审计问题：`docs/audits/DEEP_AUDIT_ISSUES.md`
- 深度审计改进：`docs/audits/DEEP_AUDIT_IMPROVEMENTS.md`
- 测试审计报告：`docs/audits/TEST_REPORT.md`
- 测试问题清单：`docs/audits/TEST_ISSUES.txt`

### 4) 平台与 GUI 专题

- Windows 构建：`docs/WINDOWS_BUILD.md`
- GUI 重构：`docs/GUI_REFACTORING.md`
- GUI 动画优化：`docs/GUI_Animation_Optimization.md`

## 迁移原则

1. 结构化、长期维护的信息优先保留在 Markdown 文档中。
2. 一次性或阶段性方案文档（尤其是 `.docx`）不再作为主知识源。
3. 计划与审计类文档统一归档到：
   - `docs/plans/`
   - `docs/audits/`
4. 新增文档需在 `README.md` 或本索引中建立入口，避免信息孤岛。
