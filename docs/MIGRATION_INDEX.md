# 文档迁移索引（清理后保留）

本文件用于说明“旧架构文档”清理后的去向，避免信息断层。

## 已清理内容范围

- `docs/` 下旧架构文档与历史 `.docx` 文档
- 仓库根目录下历史方案类 `.docx` 文件

## 当前保留与建议入口

- 项目总览与使用：`README.md`
- 变更记录：`CHANGELOG.md`
- 开发与贡献：`docs/CONTRIBUTING.md`
- 快速开始：`docs/GETTING_STARTED.md`
- 构建说明：`docs/WINDOWS_BUILD.md`
- 安全说明：`SECURITY.md`、`SECURITY_AUDIT.md`

## 迁移原则

1. 结构化、长期维护的信息优先保留在 Markdown 文档中。
2. 一次性或阶段性方案文档（尤其是 `.docx`）不再作为主知识源。
3. 新增架构/方案文档请统一使用 `docs/*.md` 并在 `README.md` 建立入口。
