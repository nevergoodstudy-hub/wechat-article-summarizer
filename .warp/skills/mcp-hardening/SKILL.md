---
name: mcp-hardening
description: "Harden the MCP server against command injection, audit log leaks, and excessive privileges. Use this skill to fix P0-4 (input validation for all tool parameters), P1-3 (audit log sensitive data sanitization), and P1-7 (directory/network access whitelisting and human-in-the-loop confirmation for dangerous operations)."
---

# MCP Server Security Hardening — P0-4, P1-3, P1-7 Fix

Secure the MCP server (25KB `server.py`) against command injection, data leakage, and privilege escalation.

## Audit Reference
- Issues: DEEP_AUDIT_ISSUES.md → P0-4, P1-3, P1-7
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P0-4, P1-3, P1-7
- Research: research_round2_security.md → Section 2

## Key Files
- MCP server: `src/wechat_summarizer/mcp/server.py`
- MCP security: `src/wechat_summarizer/mcp/security.py`
- New files to create:
  - `src/wechat_summarizer/mcp/input_validator.py`
  - `src/wechat_summarizer/mcp/audit_logger.py` (or update existing)
  - `src/wechat_summarizer/mcp/security_config.py`

## Three Sub-Tasks

### Task 1: Input Validation (P0-4)
Create `MCPInputValidator` class with methods:
- `validate_url(url)` — scheme whitelist (http/https only), hostname validation, SSRF check
- `validate_file_path(path, allowed_dirs)` — path traversal detection, directory whitelist
- `sanitize_text(text, max_length)` — length limit, null byte removal, invisible Unicode stripping
- `validate_no_shell_injection(value)` — block shell metacharacters: ; | & ` $ ( ) { } [ ] ! # ~ < > ' " \

Apply validator to EVERY tool handler in `server.py`:
1. Read server.py to find all `@mcp.tool()` decorated functions
2. Add validation calls at the start of each handler
3. Wrap in try/except MCPValidationError → return error response

### Task 2: Audit Log Sanitization (P1-3)
Create/update audit log filter:
- Regex patterns to redact: `api_key=...`, `token=...`, `sk-...`, `Bearer ...`, `password=...`
- Truncate log values > 200 chars
- Recursively sanitize nested dicts/lists
- Apply to all MCP audit log outputs

```python
SENSITIVE_PATTERNS = [
    (re.compile(r'(api[_-]?key|token|secret|password|authorization)\s*[=:]\s*\S+', re.I),
     r'\1=***REDACTED***'),
    (re.compile(r'(sk-|Bearer\s+)\S+'), r'\1***REDACTED***'),
]
```

### Task 3: Permission Restriction (P1-7)
Create `security_config.py` with:
- `allowed_dirs`: whitelist of directories tools can access
- `allowed_network_hosts`: whitelist of external hosts tools can connect to
- `max_file_size_mb`: maximum file size for operations
- `require_confirmation_for`: list of operation types needing human confirmation

Enforce in each tool handler before performing file/network operations.

## Validation
1. Test command injection payloads: `"; rm -rf /"`, `$(whoami)`, `` `id` ``
2. Test path traversal: `../../etc/passwd`, `..\..\windows\system32`
3. Test hidden Unicode instructions (zero-width characters)
4. Test log sanitization: verify API keys don't appear in log output
5. Test directory restriction: operations outside allowed_dirs are rejected
6. Existing MCP functionality still works with valid inputs
