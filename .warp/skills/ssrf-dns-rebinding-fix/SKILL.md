---
name: ssrf-dns-rebinding-fix
description: "Implement defense-in-depth SSRF protection with DNS rebinding prevention. Use this skill to fix P0-3, P1-4, P1-5: create SSRFSafeTransport for httpx that resolves DNS once and connects to the validated IP, block alternative IP notations (decimal/octal/IPv6-mapped), disable automatic HTTP redirects, and block cloud metadata endpoints."
---

# SSRF DNS Rebinding Defense — P0-3, P1-4, P1-5 Fix

Implement a custom httpx transport layer that eliminates the TOCTOU DNS rebinding window and provides comprehensive SSRF protection.

## Audit Reference
- Issues: DEEP_AUDIT_ISSUES.md → P0-3, P1-4, P1-5
- Fix plan: DEEP_AUDIT_IMPROVEMENTS.md → 方案 P0-3
- Research: research_round2_security.md → Section 1

## Covers Three Issues
1. **P0-3**: DNS rebinding (resolve-once-connect-once pattern)
2. **P1-4**: HTTP redirect validation (disable auto-redirect, validate each hop)
3. **P1-5**: Alternative IP notation blocking (decimal, octal, IPv6-mapped)

## Key Files
- Current SSRF: `src/wechat_summarizer/domain/value_objects/url.py` (`_is_private_address()`)
- New file: `src/wechat_summarizer/shared/utils/ssrf_protection.py`
- HTTP client: find httpx.AsyncClient creation points with `grep -rn "httpx.AsyncClient\|httpx.Client" src/`
- Scraper adapters: `src/wechat_summarizer/infrastructure/adapters/scrapers/`

## Implementation

### Step 1: Create SSRFSafeTransport
Create `src/wechat_summarizer/shared/utils/ssrf_protection.py` with:
- `SSRFSafeTransport(httpx.AsyncHTTPTransport)` — intercepts requests, resolves DNS, validates IP, connects to validated IP
- `is_ip_blocked(ip_str)` — checks against all private/loopback/link-local/reserved ranges + cloud metadata
- `resolve_and_validate(hostname)` — single DNS resolution + IP validation
- `SSRFBlockedError` exception class

IP ranges to block:
- 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 (RFC1918)
- 169.254.0.0/16 (link-local), ::1/128, fe80::/10, fc00::/7 (IPv6)
- ::ffff:127.0.0.0/104 (IPv6-mapped loopback)

Hostnames to block: `localhost`, `instance-data`, `metadata.google.internal`

### Step 2: Integrate with httpx clients
Find all httpx client creation and replace with safe transport:

```python
safe_client = httpx.AsyncClient(
    transport=SSRFSafeTransport(),
    follow_redirects=False,
    timeout=httpx.Timeout(30.0),
)
```

### Step 3: Add redirect handling
Implement manual redirect following with IP validation at each hop:

```python
async def safe_fetch(client, url, max_redirects=5):
    for _ in range(max_redirects):
        response = await client.get(url)
        if response.is_redirect:
            location = response.headers.get("location")
            parsed = urlparse(location)
            SSRFSafeTransport.resolve_and_validate(parsed.hostname)
            url = location
            continue
        return response
    raise TooManyRedirectsError()
```

### Step 4: Write tests
Create `tests/test_ssrf_protection.py`:
- Test blocked IPs: 127.0.0.1, 10.0.0.1, 192.168.1.1, 169.254.169.254
- Test alternative notations: 2130706433 (decimal 127.0.0.1), 0x7f000001 (hex)
- Test IPv6: ::1, ::ffff:127.0.0.1, fe80::1
- Test blocked hostnames: localhost, instance-data
- Test DNS rebinding: mock `socket.getaddrinfo` returning internal IP
- Test redirect to internal IP: mock response with Location: http://127.0.0.1/

## Validation
1. All tests in `tests/test_ssrf_protection.py` pass
2. `grep -rn "follow_redirects=True\|follow_redirects = True" src/` returns empty
3. All httpx clients use `SSRFSafeTransport`
4. Existing scraper tests still pass
