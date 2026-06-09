"""Shared network access policy tests."""

from __future__ import annotations

import pytest

from wechat_summarizer.shared.utils.network_policy import (
    DEFAULT_NETWORK_POLICY,
    NetworkAccessPolicy,
    NetworkPolicyError,
)


@pytest.mark.unit
def test_canonicalize_ip_normalizes_ipv6_mapped_ipv4() -> None:
    """IP checks should canonicalize IPv6-mapped IPv4 before policy comparison."""
    ip = DEFAULT_NETWORK_POLICY.canonicalize_ip("::ffff:127.0.0.1")

    assert str(ip) == "127.0.0.1"
    assert DEFAULT_NETWORK_POLICY.is_ip_blocked("::ffff:127.0.0.1") is True


@pytest.mark.unit
def test_require_ip_allowed_blocks_non_global_cidr_ranges() -> None:
    """Private/reserved/link-local ranges are blocked from one CIDR policy."""
    with pytest.raises(NetworkPolicyError, match="Blocked IP address"):
        DEFAULT_NETWORK_POLICY.require_ip_allowed("169.254.169.254")


@pytest.mark.unit
def test_alternative_ip_notation_is_reported() -> None:
    """Ambiguous alternate IPv4 notation should be rejected before DNS lookup."""
    assert DEFAULT_NETWORK_POLICY.looks_like_alternative_ip_notation("2130706433") is True
    assert DEFAULT_NETWORK_POLICY.looks_like_alternative_ip_notation("0177.0.0.1") is True
    assert DEFAULT_NETWORK_POLICY.looks_like_alternative_ip_notation("0x7f.0.0.1") is True


@pytest.mark.unit
def test_host_allowlist_supports_exact_and_explicit_wildcards() -> None:
    """Host allowlists should be explicit and normalized."""
    policy = NetworkAccessPolicy(allowed_hosts=("api.example.com", "*.assets.example.com"))

    assert policy.is_host_allowed("API.EXAMPLE.COM.") is True
    assert policy.is_host_allowed("cdn.assets.example.com") is True
    assert policy.is_host_allowed("assets.example.com") is False
    assert policy.is_host_allowed("evil-api.example.com") is False


@pytest.mark.unit
def test_blocked_hostname_wins_over_empty_allowlist() -> None:
    """Blocked hostnames are denied even when no allowlist is configured."""
    with pytest.raises(NetworkPolicyError, match="Blocked hostname"):
        DEFAULT_NETWORK_POLICY.require_host_allowed("metadata.google.internal")
