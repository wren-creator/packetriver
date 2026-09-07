"""A scripted diner patron. Every few seconds it signs in to the rewards
portal and checks its mail, all in cleartext over the open Wi-Fi segment.
Nothing here is an exploit; it just keeps the wire warm so an attacker who
gets between this box and the AP has something to catch.
"""
from __future__ import annotations

import os
import socket
import ssl
import time
import urllib.parse
import urllib.request

AP = os.environ.get("AP_HOST", "172.31.60.10")
USER = os.environ.get("PORTAL_USER", "diner_guest")
PASS = os.environ.get("PORTAL_PASS", "Rewards2026")
EVERY = int(os.environ.get("EVERY_SECONDS", "4"))
TLS = os.environ.get("NETLAB_TLS", "0") == "1"
_SCHEME = "https" if TLS else "http"
_POP_PORT = 995 if TLS else 110
_NOVERIFY = ssl._create_unverified_context() if TLS else None   # self-signed lab cert


def portal_login():
    data = urllib.parse.urlencode({"user": USER, "pass": PASS}).encode()
    try:
        urllib.request.urlopen(f"{_SCHEME}://{AP}/login", data=data, timeout=5,
                               context=_NOVERIFY).read()
    except OSError as exc:
        print(f"[patron] portal: {exc}")


def check_mail():
    try:
        s = socket.create_connection((AP, _POP_PORT), timeout=5)
        if TLS:
            s = _NOVERIFY.wrap_socket(s, server_hostname=AP)
    except OSError as exc:
        print(f"[patron] pop3: {exc}")
        return
    f = s.makefile("rwb", buffering=0)
    try:
        f.readline()
        for cmd in (f"USER booth7", f"PASS {PASS}", "STAT", "RETR 1", "QUIT"):
            f.write((cmd + "\r\n").encode())
            f.readline()
            if cmd == "RETR 1":
                # drain the message body
                while True:
                    ln = f.readline()
                    if not ln or ln.strip() == b".":
                        break
    finally:
        s.close()


if __name__ == "__main__":
    print(f"[patron] talking to the AP at {AP} every {EVERY}s, in the clear")
    while True:
        portal_login()
        check_mail()
        time.sleep(EVERY)
