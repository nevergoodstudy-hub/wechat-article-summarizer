---
name: wechat-project-3round-audit
description: Conduct deep three-round web-backed audits for the WeChat Article Summarizer project. Use when tasks require analyzing runtime mechanics, producing graded issue inventories, and generating issue-to-fix mappings with source-backed recommendations and local markdown deliverables.
---
# WeChat Project 3-Round Audit
1. Confirm scope and artifacts:
- Runtime mechanism report (`.md`)
- Graded issue report (`.md`)
- Targeted improvement report (`.md`)
2. Map current implementation from local codebase:
- Read entrypoints, config/container wiring, use cases, adapters, security utilities, MCP server, and tests.
- Build runtime flow from startup to shutdown, including CLI, GUI, and MCP paths.
3. Run web research in 3 rounds, each with at least 50 relevant webpages:
- Round 1: architecture, layering, DI, concurrency, plugin boundaries.
- Round 2: security, secret handling, SSRF/rebinding, auth/session, logging redaction, supply chain.
- Round 3: test strategy, reliability, performance, packaging/release hardening.
4. For each round:
- Record sources and primary facts.
- Separate direct evidence from inferred conclusions.
- Resolve contradictions explicitly.
5. Produce graded issues:
- P0 Critical: immediate security/data-loss/remote exploit risks.
- P1 High: major correctness/reliability/privacy risks.
- P2 Medium: maintainability/performance/testability risks.
- P3 Low: style/docs/minor DX gaps.
6. Produce targeted improvements for each issue:
- Fix objective and expected risk reduction.
- Exact code-level direction (module/function scope).
- Validation steps (tests/lint/type/security checks).
- Source-backed external references and at least one real-world implementation reference where possible.
7. Save all outputs in project root as markdown files and provide concise completion summary.
