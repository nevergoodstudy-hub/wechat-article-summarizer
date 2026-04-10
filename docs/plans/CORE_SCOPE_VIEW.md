# 核心改造视图（Core Scope View）

> 目标：在“深度焕新”执行期，统一团队默认关注范围，降低全仓噪音对检索、评审、回归的干扰。

## 1. 默认改造范围（Core In-Scope）

以下路径是本轮焕新的默认执行范围：

- `src/wechat_summarizer/`（核心业务源码）
- `tests/`（测试与回归）
- `.github/workflows/`（CI 门禁）
- `pyproject.toml`（工具链与测试配置）
- `docs/plans/`、`docs/audits/`（方案与审计沉淀）

## 2. 默认排除范围（Noise Out-of-Scope）

以下路径默认视为噪音目录，除非任务明确要求，不进入改造与评审主流程：

- `.mypy_cache/`
- `.tmp_skillhub_sync/`
- `.warp/`
- `target/`
- `apps/desktop/node_modules/`
- `apps/desktop/.vite/`

## 3. 本地执行建议（仅扫描核心范围）

### 统一质量门禁入口（推荐）

```bash
python scripts/quality_gate.py --mode lint
python scripts/quality_gate.py --mode mypy
python scripts/quality_gate.py --mode test
python scripts/quality_gate.py --mode security-smoke
```

### 底层命令（必要时）

```bash
ruff check src/wechat_summarizer tests
ruff format --check src/wechat_summarizer tests
mypy src/wechat_summarizer --ignore-missing-imports
pytest tests -v
```

## 4. MCP 入参校验基线（Batch 3）

本轮已执行以下统一化规则：

1. MCP 工具参数优先走 `src/wechat_summarizer/mcp/input_validator.py`。
2. 对于整数范围参数，统一使用 `validate_int_range(...)`，避免工具函数内重复手写范围判断。
3. URL 列表数量上限统一由 `validate_urls(...)` 控制，业务循环不再做二次截断（如 `urls[:10]`）。

落地示例：

- `get_audit_logs(limit)` 使用统一整数范围校验。
- `batch_summarize` 与 `track_topic` 移除重复的 `urls[:10]` 业务截断，改为依赖校验层。

## 5. PR 评审约定

1. 优先评审 Core In-Scope 变更。  
2. 若 PR 包含 Noise Out-of-Scope 路径，需在描述中说明必要性。  
3. 安全与门禁相关改动需附验证结果（至少包含失败用例覆盖说明）。

## 6. 与现有治理文档关系

- 目录边界基线：`docs/PROJECT_STRUCTURE.md`
- 仓库整理周期：`docs/plans/REPO_HYGIENE_CYCLE.md`
- 深度焕新总方案：`docs/plans/DEEP_RENEWAL_FEASIBILITY_PLAN.md`
- 执行设计：`docs/superpowers/specs/2026-04-03-deep-renewal-execution-design.md`
- 实施计划：`docs/superpowers/specs/2026-04-03-deep-renewal-implementation-plan.md`
