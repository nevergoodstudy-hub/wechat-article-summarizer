# Round 2 Research: Security, SSRF Prevention, MCP Vulnerabilities & DNS Rebinding

## Research Date: 2026-02-19
## Scope: SSRF/DNS Rebinding defense, MCP security best practices, Python secret management, audit logging

---

## 1. SSRF Prevention & DNS Rebinding in Python

### Key Findings

#### 1.1 DNS Rebinding Attack Pattern
- DNS rebinding is a TOCTOU (Time-of-Check-Time-of-Use) vulnerability: the hostname is validated against a blocklist on first DNS lookup, but the actual HTTP request triggers a second DNS lookup that resolves to a different (internal) IP.
- Attackers set TTL=0 on DNS records so the IP changes between validation and request.
- This bypasses all hostname/IP blocklist-based SSRF protections that validate before the request.

#### 1.2 Proper SSRF Defense (Defense-in-Depth)
- **Resolve Once, Use Once**: Resolve the hostname to IP once, validate that IP, then force the HTTP request to use that specific IP (set `Host` header manually). This is the AutoGPT fix pattern.
- **Block Private/Internal IP Ranges**: Check against `ipaddress.is_private`, `is_loopback`, `is_link_local`, `is_reserved`. Include cloud metadata IPs (169.254.169.254, `instance-data` hostname).
- **Disable HTTP Redirects**: Redirects can redirect to internal IPs after the initial check. Either disable redirects or re-validate each redirect target.
- **Alternative IP Notation Blocking**: Block decimal notation (2130706433 = 127.0.0.1), IPv6-mapped IPv4 (::ffff:127.0.0.1), octal (0177.0.0.1).
- **Network Egress Filtering**: Don't rely solely on application code; use firewall rules / WAF to block outbound traffic to internal ranges.
- **OWASP Recommendation**: For user-controlled URLs (webhooks, image URLs), use allowlists when possible. When not possible, validate + resolve + check IP ranges.

#### 1.3 Real-World Bypass Examples (2025)
- **AutoGPT GHSA-wvjg-9879-3m7w**: SSRF protection bypassed via DNS rebinding because validate_url() and actual request used separate DNS lookups.
- **BentoML CVE-2025-54381**: Initial SSRF patch had incomplete blocklist (missing `instance-data` hostname, alternative IP notations).
- **MindsDB GHSA-4jcv-vp96-94xr**: DNS rebinding bypassed entire website's SSRF protection.

#### 1.4 httpx-Specific SSRF Protection
- httpx does not have built-in SSRF protection. Must implement custom transport or event hooks.
- Pattern: Create a custom `httpx.AsyncHTTPTransport` that resolves DNS, validates IP, then connects to the validated IP with Host header override.
- Must also handle IPv6 addresses and dual-stack resolution.

### Relevance to This Project
- **WARN-005**: The project's SSRF protection lacks DNS rebinding defense. URL validation and HTTP request use separate DNS lookups.
- httpx is used for article scraping — a user-provided URL could exploit DNS rebinding to access internal services.
- No redirect validation exists — an external URL could redirect to 127.0.0.1/internal-service.
- No alternative IP notation blocking (decimal, octal, IPv6-mapped).

---

## 2. MCP Security Best Practices & Vulnerabilities

### Key Findings

#### 2.1 MCP Specification Security Concerns
- **MCP SDK CVE-2025-66416**: The Python MCP SDK lacked default DNS rebinding protection for HTTP-based servers. FastMCP with streamable HTTP/SSE transport was vulnerable when running on localhost without authentication.
- **Session IDs in URLs**: The protocol mandates session identifiers in URLs, violating security best practices (exposes in logs, enables session hijacking).
- **Lack of Authentication Standards**: The protocol provides minimal guidance on authentication, leading to weak implementations.
- **Missing Integrity Controls**: No required message signing or verification, allowing message tampering.
- **OAuth was only added in March 2025**; many servers still don't use it.

#### 2.2 Critical MCP Attack Vectors (Palo Alto Unit42, Red Hat)
1. **Prompt Injection via Tool Descriptions**: Malicious MCP servers can embed hidden instructions in tool descriptions that the AI follows.
2. **Tool Shadowing / Impersonation**: Malicious servers provide tools with names similar to legitimate ones.
3. **Token Theft**: MCP servers store OAuth tokens; compromise = access to all connected services.
4. **Command Injection**: If server doesn't sanitize inputs, `os.system(f"convert {filepath}")` allows shell injection.
5. **Data Exfiltration**: Through legitimate channels — the AI can be tricked into sending data to external addresses.
6. **Rugpull**: Server changes behavior after gaining trust (tool definitions change post-installation).
7. **Credential Harvesting**: Malicious servers read environment variables (AWS_SECRET_KEY, OPENAI_API_KEY, etc.).

#### 2.3 MCP Security Best Practices
- **Sandboxing**: Launch MCP servers with restricted file system and network access. Use containers, chroot, or application sandboxes.
- **Least Privilege**: Only expose necessary tools. Use fine-grained RBAC per user/role.
- **Input Validation**: Always sanitize data before using as arguments for functions that execute commands.
- **Human-in-the-Loop**: The MCP spec says "there SHOULD always be a human in the loop" — treat as MUST.
- **Audit Logging**: Each agent action should produce structured log entries with user identity, timestamp, session ID, tool invoked, and parameters.
- **Per-user OAuth**: Use per-user authentication flows, not shared organizational tokens.
- **SCA & SAST**: Include MCP components in standard vulnerability management pipelines.

### Relevance to This Project
- **WARN-003**: MCP audit log sanitization is insufficient — sensitive data may leak into logs.
- The project's MCP server (25KB) needs command injection protection, input validation on all tool parameters.
- No sandboxing or privilege restriction for the MCP server.
- No human-in-the-loop confirmation for destructive operations.
- DNS rebinding protection must be enabled for localhost-bound MCP server.
- Tool descriptions should be reviewed for prompt injection safety.

---

## 3. PBKDF2 & Secret Management

### Key Findings

#### 3.1 PBKDF2 Salt Best Practices
- Salt MUST be randomly generated per credential, minimum 16 bytes, using `os.urandom()`.
- **Fixed/hardcoded salts** are a critical vulnerability — rainbow table attacks become feasible.
- The project's `_get_or_create_salt()` may have been partially fixed, but must verify:
  - Salt is stored securely (not in plaintext in config).
  - Each credential gets its own salt.
  - Salt length is ≥16 bytes.

#### 3.2 Python Secret Management
- Use `keyring` library for OS-level credential storage (Windows Credential Manager, macOS Keychain, Linux Secret Service).
- Never store API keys in plaintext config files.
- Use environment variables or encrypted vaults for sensitive configuration.
- Python 3.14+ `secrets` module for cryptographic random generation.

### Relevance to This Project
- **WARN-002**: Investigate whether the PBKDF2 salt fix is complete. Verify per-credential salt, minimum 16 bytes, secure storage.
- API keys for LLM services (OpenAI, Anthropic, Zhipu) must not be stored in plaintext.
- Consider using `keyring` for OS-level secure storage of API keys.

---

## 4. Supply Chain & Dependency Security

### Key Findings

#### 4.1 Dependency Risks
- MCP-related packages have had critical vulnerabilities: `mcp-remote` (CVE-2025-6514, RCE), unofficial Postmark MCP server (email BCC exfiltration).
- Over 1,800 MCP servers found on the public internet without authentication.
- All dependencies should be pinned, audited with `pip-audit` or `safety`, and scanned in CI.

#### 4.2 Best Practices
- Use `pip-audit` for vulnerability scanning.
- Pin all dependencies with hash verification (`pip install --require-hashes`).
- Use `dependabot` or `renovate` for automated dependency updates.
- Review and minimize direct dependencies.

### Relevance to This Project
- No `pip-audit` or dependency scanning in the project.
- `pyproject.toml` dependencies should be reviewed for known vulnerabilities.
- MCP SDK version should be checked for CVE-2025-66416 fix.

---

## Summary of Security Issues Found

| Issue | Severity | Category |
|-------|----------|----------|
| SSRF lacks DNS rebinding protection | P0 | Security |
| MCP server missing input validation / command injection risk | P0 | Security |
| MCP audit log leaks sensitive data | P1 | Security |
| No redirect validation in SSRF checks | P1 | Security |
| Alternative IP notation bypasses not blocked | P1 | Security |
| PBKDF2 salt implementation needs verification | P1 | Security |
| MCP server no sandboxing / privilege restriction | P1 | Security |
| No human-in-the-loop for MCP destructive ops | P2 | Security |
| API keys potentially in plaintext config | P2 | Security |
| No dependency vulnerability scanning (pip-audit) | P2 | Supply Chain |
| MCP SDK version not checked for known CVEs | P2 | Supply Chain |
| No DNS rebinding protection on MCP localhost server | P2 | Security |
