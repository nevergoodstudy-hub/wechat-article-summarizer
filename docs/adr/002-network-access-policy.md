# ADR-002: Centralize SSRF-Safe Network Access

## Status
Accepted

## Context
Article scraping and export workflows accept user-provided URLs. These paths need SSRF protection against private ranges, cloud metadata endpoints, redirect abuse, DNS rebinding and alternative IP notation.

## Decision
Route user URL fetching through a shared network access policy and safe fetch helpers. The policy validates hosts, canonicalized IP addresses and redirect targets before network access.

## Rationale
A single policy avoids scattered allow and block logic. It also gives tests one authoritative place to prove SSRF controls for CLI, GUI, MCP and exporter surfaces.

## Trade-offs
Centralization can make unusual scraper exceptions harder to add. The safer default is to require explicit policy changes rather than allowing each adapter to bypass checks.

## Consequences
- Positive: URL validation, redirect validation and IP canonicalization share one security model.
- Negative: Some legitimate non-public hosts are blocked unless explicitly allowed.
- Mitigation: Keep allowlist support in the policy and cover exceptions with targeted tests.

