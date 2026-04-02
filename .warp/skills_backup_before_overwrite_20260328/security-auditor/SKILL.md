---
name: security-auditor
description: "Audit and fix security issues in the WeChat Article Summarizer project. Use this skill for security-related code fixes including: PBKDF2 salt hardening, MCP audit log sanitization improvements, and SSRF DNS rebinding protection. Targets WARN-002, WARN-003, WARN-005 from TEST_ISSUES.txt."
---

# Security Auditor Agent

Investigate and fix security warnings in the WeChat Article Summarizer project.

## Project Context
- Python 3.10+ project, source in `src/wechat_summarizer/`
- Security module: `src/wechat_summarizer/shared/utils/security.py`
- MCP security: `src/wechat_summarizer/mcp/security.py`
- URL validation: `src/wechat_summarizer/domain/value_objects/url.py`

## Security Issues

### WARN-002: PBKDF2 fixed salt value
- File: `src/wechat_summarizer/shared/utils/security.py`
- Problem: Check if PBKDF2 key derivation still uses a fixed salt `b"wechat_summarizer_v2"`. If a `_get_or_create_salt()` function exists and uses `secrets.token_bytes()`, this may already be fixed.
- Verify: Read the file and confirm the salt is randomly generated and persisted.
- If not fixed: Replace fixed salt with `os.urandom(16)` or `secrets.token_bytes(32)`, persist in a salt file.

### WARN-003: MCP audit log sanitization incomplete
- File: `src/wechat_summarizer/mcp/security.py` (`AuditLogger._sanitize_args`)
- Problem: Only checks key names for sensitive words, doesn't inspect string values for API key patterns or truncate long strings.
- Fix:
  1. Add string length truncation (>200 chars → truncate with "...[truncated]")
  2. Add regex check for API key patterns in values (e.g., `sk-`, `key-`, base64-like long strings)
  3. Recursively sanitize nested dict/list values

### WARN-005: SSRF no DNS rebinding protection
- File: `src/wechat_summarizer/domain/value_objects/url.py`
- Problem: `_is_private_address()` only checks hostname strings, not resolved IPs. DNS rebinding can bypass this.
- Fix approach: Document the limitation and add a utility function for connection-level IP checking that can be used by the HTTP client layer. Add a `validate_resolved_ip()` function.

## Execution Steps
1. Read each affected file
2. Assess the current state (some issues may already be fixed)
3. Apply targeted fixes
4. Report findings and changes
