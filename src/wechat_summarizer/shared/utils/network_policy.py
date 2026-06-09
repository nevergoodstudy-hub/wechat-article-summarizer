"""Shared network access policy for SSRF-sensitive outbound requests."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

IPAddress = ipaddress.IPv4Address | ipaddress.IPv6Address
IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network

DEFAULT_BLOCKED_NETWORKS: tuple[IPNetwork, ...] = (
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.88.99.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("ff00::/8"),
)

DEFAULT_BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
    {
        "localhost",
        "instance-data",
        "metadata.google.internal",
        "metadata.internal",
        "169.254.169.254",
        "fd00:ec2::254",
    }
)


class NetworkPolicyError(ValueError):
    """Network access policy violation."""


@dataclass(frozen=True)
class NetworkAccessPolicy:
    """Validate outbound host/IP access from one policy entry point.

    OWASP SSRF guidance recommends canonicalizing IPs before comparison and
    using allowlists for destinations that can be constrained. This policy keeps
    host allowlists, blocked hostnames, and blocked CIDR checks together so MCP
    input validation and HTTP transport validation cannot drift apart.
    """

    allowed_hosts: tuple[str, ...] = ()
    blocked_hostnames: frozenset[str] = DEFAULT_BLOCKED_HOSTNAMES
    blocked_networks: tuple[IPNetwork, ...] = DEFAULT_BLOCKED_NETWORKS

    @staticmethod
    def normalize_host(host: str) -> str:
        """Normalize a host name for policy comparisons."""
        normalized = host.strip().lower().rstrip(".")
        if normalized.startswith("[") and normalized.endswith("]"):
            normalized = normalized[1:-1]
        return normalized

    def canonicalize_ip(self, value: str) -> IPAddress:
        """Parse and canonicalize an IP address before policy comparison."""
        ip = ipaddress.ip_address(value)
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
            return ip.ipv4_mapped
        return ip

    def is_ip_blocked(self, value: str) -> bool:
        """Return whether an IP address is blocked by public-network policy."""
        try:
            ip = self.canonicalize_ip(value)
        except ValueError:
            return True

        if not ip.is_global:
            return True

        return any(ip in network for network in self.blocked_networks)

    def require_ip_allowed(self, value: str) -> IPAddress:
        """Return canonical IP if allowed, otherwise raise NetworkPolicyError."""
        try:
            ip = self.canonicalize_ip(value)
        except ValueError as exc:
            raise NetworkPolicyError(f"Invalid IP address: {value}") from exc

        if self.is_ip_blocked(str(ip)):
            raise NetworkPolicyError(f"Blocked IP address: {ip}")

        return ip

    def looks_like_alternative_ip_notation(self, host: str) -> bool:
        """Detect IPv4 alternate notations that URL parsers may disagree on."""
        normalized = self.normalize_host(host)

        if normalized.isdigit():
            return True

        if normalized.startswith("0x"):
            return True

        parts = normalized.split(".")
        if len(parts) == 4 and all(part for part in parts):
            if all(part.isdigit() for part in parts):
                return any(len(part) > 1 and part.startswith("0") for part in parts)
            return any(part.lower().startswith("0x") for part in parts)

        return False

    def is_host_allowed(self, host: str) -> bool:
        """Return whether a host is allowed by the configured allowlist."""
        normalized_host = self.normalize_host(host)
        if not normalized_host or normalized_host in self.blocked_hostnames:
            return False

        if not self.allowed_hosts:
            return True

        for allowed in self.allowed_hosts:
            normalized_allowed = self.normalize_host(allowed)
            if not normalized_allowed:
                continue
            if normalized_allowed.startswith("*."):
                suffix = normalized_allowed[1:]
                if normalized_host.endswith(suffix) and normalized_host != normalized_allowed[2:]:
                    return True
            elif normalized_host == normalized_allowed:
                return True

        return False

    def require_host_allowed(self, host: str) -> str:
        """Return normalized host if allowed, otherwise raise NetworkPolicyError."""
        normalized_host = self.normalize_host(host)
        if normalized_host in self.blocked_hostnames:
            raise NetworkPolicyError(f"Blocked hostname: {host}")
        if self.looks_like_alternative_ip_notation(normalized_host):
            raise NetworkPolicyError(f"Blocked alternative IP notation: {host}")
        if not self.is_host_allowed(normalized_host):
            raise NetworkPolicyError(f"Host not allowed by network policy: {host}")
        return normalized_host


DEFAULT_NETWORK_POLICY = NetworkAccessPolicy()
