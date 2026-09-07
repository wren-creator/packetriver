#!/usr/bin/env python3
"""Lab-only target guard.

Import `guard(host)` and call it before any script hits a target, or run this
file directly with a host argument. It refuses anything that is not a Packet
River container / network, so a stray copy-paste can't be pointed at the
outside world.
"""
from __future__ import annotations

import ipaddress
import socket
import sys

ALLOWED_NAMES = {
    "gateway", "simmap", "scoring", "bus", "db", "websites", "paygw",
    "bank", "as400", "z16", "netlab", "traffic-plc", "rail-plc", "field-plc",
    "generalstore.town.local",
}
ALLOWED_NETS = [ipaddress.ip_network("172.31.0.0/16")]


def guard(host: str) -> None:
    if host in ALLOWED_NAMES:
        return
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        try:
            ip = ipaddress.ip_address(socket.gethostbyname(host))
        except Exception:
            sys.exit(f"[guard] refusing unknown host: {host}")
    if any(ip in n for n in ALLOWED_NETS):
        return
    sys.exit(f"[guard] refusing non-lab target: {host} ({ip})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: targets.py <host>")
    guard(sys.argv[1])
    print(f"[guard] {sys.argv[1]} is in scope")
