"""The homeowner: a rail engineer who signs in to the crew portal over plain
HTTP every few seconds from the couch. Not an exploit, just keeps the home LAN
carrying a credential worth catching.
"""
from __future__ import annotations

import os
import time
import urllib.parse
import urllib.request

PORTAL = os.environ.get("PORTAL_URL", "http://172.31.61.10/portal/rail/login")
CREW_USER = os.environ.get("CREW_USER", "rse.kmiller")
CREW_PASS = os.environ.get("CREW_PASS", "Sw1tchboard!")
EVERY = int(os.environ.get("EVERY_SECONDS", "5"))


if __name__ == "__main__":
    print(f"[resident] crew portal check-in every {EVERY}s as {CREW_USER}, cleartext")
    body = urllib.parse.urlencode({"user": CREW_USER, "pass": CREW_PASS}).encode()
    while True:
        try:
            urllib.request.urlopen(PORTAL, data=body, timeout=5).read()
        except OSError as exc:
            print(f"[resident] portal: {exc}")
        time.sleep(EVERY)
