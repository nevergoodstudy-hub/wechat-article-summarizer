## Added
- Added docs quality gate in CI via `mkdocs build --strict`.
- Added `docs` optional dependency group (MkDocs, Material, mkdocstrings, pymdown-extensions).
- Added optional MCP HTTP header authentication via `X-MCP-Token`.
- Added strict Microsoft Store packaging mode: `scripts/build_msix.py --store`.

## Changed
- MCP HTTP now binds to `127.0.0.1` by default to reduce exposure.
- Remote bind now requires explicit opt-in (`--allow-remote`) with warning logs.
- MCP CLI/server now supports `host`, `auth_token`, and `allow_remote` parameters.
- MSIX identity fields are now parameterized by env vars:
  - `MSIX_IDENTITY_NAME`
  - `MSIX_PUBLISHER`
  - `MSIX_VERSION`
- CI quality gates tightened: mypy / pip-audit / bandit are now blocking.
- Cleaned up `mkdocs.yml` and fixed search language config format.

## Fixed
- Fixed MCP URL hostname validation compatibility issue while preserving SSRF protection.
- Fixed mismatch between MSIX manifest icon names and packaging assets.
- Fixed missing manifest-asset consistency validation in MSIX build flow.

## Security
- Default MCP HTTP external exposure reduced by localhost-only default.
- Added minimal token-based protection for HTTP transport.
