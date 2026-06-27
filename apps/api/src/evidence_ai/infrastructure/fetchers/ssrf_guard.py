"""Protección SSRF — bloquea fetches a IPs internas, loopback y metadata cloud."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


# IPv4 ranges privadas + bloqueadas
_BLOCKED_NETWORKS_V4 = [
    ipaddress.ip_network(net)
    for net in (
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8",        # loopback
        "169.254.0.0/16",     # link-local (incluye metadata AWS/GCP/Azure)
        "0.0.0.0/8",
        "100.64.0.0/10",      # CGNAT
    )
]
_BLOCKED_NETWORKS_V6 = [
    ipaddress.ip_network(net)
    for net in ("::1/128", "fc00::/7", "fe80::/10")
]


class SSRFBlocked(Exception):
    pass


def assert_url_is_safe(url: str) -> None:
    """Lanza SSRFBlocked si la URL apunta a una red privada o esquema no permitido."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise SSRFBlocked(f"Esquema no permitido: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlocked("URL sin hostname")

    # Resolver hostname → IPs
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as e:
        raise SSRFBlocked(f"No se pudo resolver {hostname}: {e}") from e

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if isinstance(ip, ipaddress.IPv4Address):
            for net in _BLOCKED_NETWORKS_V4:
                if ip in net:
                    raise SSRFBlocked(f"IP {ip} en red bloqueada {net}")
        else:
            for net in _BLOCKED_NETWORKS_V6:
                if ip in net:
                    raise SSRFBlocked(f"IPv6 {ip} en red bloqueada {net}")
