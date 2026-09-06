#!/usr/bin/env python3
"""Quick recon sweep of the Packet River lab network.

    recon.py            # scan the known hosts
    recon.py <host>     # port-scan one host

Thin wrapper over nmap, guarded to lab targets only.
"""
import subprocess
import sys

sys.path.insert(0, "/opt/pktr/scripts")
from targets import ALLOWED_NAMES, guard  # noqa: E402

PORTS = "21,22,80,443,502,503,1883,3306,8000,8001,8080,8090,8093"


def scan(host):
    guard(host)
    print(f"\n=== {host} ===")
    subprocess.run(["nmap", "-Pn", "-sV", "--open", "-p", PORTS, host])


def main():
    if len(sys.argv) > 1:
        scan(sys.argv[1])
        return
    for h in ("gateway", "websites", "field-plc", "scoring", "bus"):
        if h in ALLOWED_NAMES:
            scan(h)


if __name__ == "__main__":
    main()
