#!/usr/bin/env python3
"""Quick recon sweep of the Packet River lab network.

    recon.py            # DNS sweep + port-scan the known hosts
    recon.py <host>     # port-scan one host
    recon.py dns        # just the name-server work (zone transfer)
    recon.py rev        # reverse-DNS sweep (the reverse zone is AXFR-able too)

Thin wrapper over dig + nmap, guarded to lab targets only.
"""
import subprocess
import sys

sys.path.insert(0, "/opt/pktr/scripts")
from targets import ALLOWED_NAMES, guard  # noqa: E402

PORTS = "21,22,80,443,502,503,1883,3306,8000,8001,8080,8090,8093"
ZONE = "packetriver.range"


def dns_sweep():
    guard("dns")
    print(f"\n=== DNS: the {ZONE} name server ===", flush=True)
    subprocess.run(["dig", "+noall", "+answer", "@172.31.20.253", ZONE, "SOA"])
    print("\n--- trying a zone transfer (AXFR) ---", flush=True)
    r = subprocess.run(
        ["dig", "+noall", "+answer", "+time=3", "+tries=1", "AXFR", ZONE, "@172.31.20.253"],
        capture_output=True, text=True,
    )
    print(r.stdout, end="")
    if "Transfer failed" in r.stderr or not r.stdout.strip():
        print(r.stderr, end="")
        print("[recon] no zone transfer - name server is not offering AXFR")
    else:
        n = len([l for l in r.stdout.splitlines() if l.strip()])
        print(f"[recon] pulled {n} records. Read every line - not just the A/CNAMEs.")


def reverse_sweep():
    guard("dns")
    rev = "20.31.172.in-addr.arpa"
    print(f"\n=== reverse DNS: {rev} ===", flush=True)
    r = subprocess.run(
        ["dig", "+noall", "+answer", "+time=3", "+tries=1", "AXFR", rev, "@172.31.20.253"],
        capture_output=True, text=True,
    )
    print(r.stdout, end="")
    if not r.stdout.strip():
        print("[recon] no reverse transfer; try one at a time: "
              "for i in $(seq 2 254); do dig +short -x 172.31.20.$i @172.31.20.253; done")
    else:
        print("[recon] the reverse zone names every box it knows. cross-check against the forward zone.")


def scan(host):
    guard(host)
    print(f"\n=== {host} ===", flush=True)
    subprocess.run(["nmap", "-Pn", "-sV", "--open", "-p", PORTS, host])


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "dns":
            dns_sweep()
        elif arg in ("rev", "reverse"):
            reverse_sweep()
        else:
            scan(arg)
        return
    dns_sweep()
    for h in ("gateway", "websites", "field-plc", "scoring", "bus"):
        if h in ALLOWED_NAMES:
            scan(h)


if __name__ == "__main__":
    main()
