#!/usr/bin/env python3
"""net-snmp pass_persist backend for the Widget Works line-management subtree
(.1.3.6.1.4.1.53864.1).

  .1.0  lineEnable   INTEGER   read-write   1 = line running, 0 = stopped
  .2.0  lineSpeed    INTEGER   read-write   commanded line speed, %
  .3.0  opsNote      STRING    read-only    this run's reconciliation key
  .4.0  agentUptime  INTEGER   read-only

Writing lineEnable=0 over the `private` community stops the assembly line -
the pass_persist backend publishes it to the event bus and simmap mirrors it
onto the map. Same physical result as the Modbus path, a different plane.
"""
import os
import subprocess
import sys
import time

BASE = ".1.3.6.1.4.1.53864.1"
STATE = "/tmp/line.state"
START = time.time()
MQTT_HOST = os.environ.get("MQTT_HOST", "bus")

FLAG = "PKTR{factory_snmp_flag_missing}"
try:
    with open("/run/secret/factory_snmp/flag.txt") as fh:
        FLAG = fh.read().strip()
except OSError:
    pass


def _load():
    try:
        with open(STATE) as fh:
            a, b = fh.read().split()
            return int(a), int(b)
    except (OSError, ValueError):
        return 1, 70          # lineEnable, lineSpeed


def _save(en, sp):
    try:
        with open(STATE, "w") as fh:
            fh.write(f"{en} {sp}")
    except OSError:
        pass


def _publish(stopped: bool):
    try:
        subprocess.run(
            ["mosquitto_pub", "-h", MQTT_HOST, "-t", "pkt/factory/cmd",
             "-m", '{"stop": %s, "src": "snmp"}' % ("true" if stopped else "false")],
            timeout=5, check=False)
    except (OSError, subprocess.SubprocessError):
        pass


def _oids():
    en, sp = _load()
    return {
        f"{BASE}.1.0": ("integer", en),
        f"{BASE}.2.0": ("integer", sp),
        f"{BASE}.3.0": ("string", FLAG),
        f"{BASE}.4.0": ("integer", int(time.time() - START)),
    }


def _emit(oid, typ, val):
    sys.stdout.write(f"{oid}\n{typ}\n{val}\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        cmd = line.strip()
        if cmd == "PING":
            sys.stdout.write("PONG\n")
            sys.stdout.flush()
        elif cmd == "get":
            oid = sys.stdin.readline().strip()
            o = _oids().get(oid)
            if o:
                _emit(oid, o[0], o[1])
            else:
                sys.stdout.write("NONE\n")
                sys.stdout.flush()
        elif cmd == "getnext":
            oid = sys.stdin.readline().strip()
            keys = list(_oids())
            nxt = next((k for k in keys if _oid_gt(k, oid)), None)
            if nxt:
                o = _oids()[nxt]
                _emit(nxt, o[0], o[1])
            else:
                sys.stdout.write("NONE\n")
                sys.stdout.flush()
        elif cmd == "set":
            oid = sys.stdin.readline().strip()
            spec = sys.stdin.readline().strip()          # "integer 0"
            en, sp = _load()
            try:
                _, raw = spec.split(None, 1)
                num = int(raw)
            except ValueError:
                sys.stdout.write("wrong-type\n")
                sys.stdout.flush()
                continue
            if oid == f"{BASE}.1.0":
                _save(num, sp)
                _publish(stopped=(num == 0))
                sys.stdout.write("DONE\n")
            elif oid == f"{BASE}.2.0":
                _save(en, num)
                sys.stdout.write("DONE\n")
            else:
                sys.stdout.write("not-writable\n")
            sys.stdout.flush()
        else:
            sys.stdout.write("NONE\n")
            sys.stdout.flush()


def _oid_gt(a, b):
    def parts(s):
        return [int(x) for x in s.strip(".").split(".") if x.isdigit()]
    return parts(a) > parts(b)


if __name__ == "__main__":
    main()
