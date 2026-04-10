# 项目结构与边界约定

本文件定义仓库顶层目录职责，避免文件再次回流到根目录或跨域堆积。

## 顶层目录职责

- `src/`：主应用源码（Python）
- `tests/`：测试代码
- `docs/`：长期维护文档（架构/计划/审计/指南）
- `scripts/`：构建、维护、自动化脚本
- `research/`：研究与探索材料
- `verification_reports/`：可再生产物（tooling/tests/security）
- `specs/`：打包与发布 spec
- `assets/`：静态资产
- `apps/`：子应用（如桌面端）
- `services/`：服务端/网关相关子工程

## 根目录保留白名单（建议）

仅保留以下类型文件：

1. 仓库元信息：`README.md`、`LICENSE`、`CHANGELOG.md`
2. 构建与依赖：`pyproject.toml`、`Cargo.lock`、`mkdocs.yml`
3. 运行入口：`run_gui.pyw`、`start_silent.vbs`
4. 安全与协作：`SECURITY.md`、`AGENTS.md`
5. 其他确需根目录驻留的系统文件（如 `.editorconfig`、`.gitignore`）

其余文档/日志/一次性脚本应下沉至对应目录。

## 大体量目录治理约定

### `apps/desktop/`
- `node_modules/`、`.vite/`、`*.tsbuildinfo` 不应纳入版本控制。
- 若历史已入库，后续建议在独立变更中执行索引清理（`git rm --cached`）并保留锁文件。

### `services/`
- 每个子服务应有最小说明文档（README 或 docs 链接）。
- 服务级配置/部署脚本不应散落到仓库根目录。

### `wechat-article-summarizer/`
- 该目录当前仅保留缓存/临时产物时，应保持忽略并避免新增可跟踪内容。

## 变更流程（新增目录或大文件）

1. 先确认是否已有职责匹配目录。
2. 若新增顶层目录，必须同步更新：
   - `README.md` 文档入口
   - `docs/README.md` 或本文件
3. 大文件（>10MB）需给出必要性说明，并优先使用外部制品存储。
