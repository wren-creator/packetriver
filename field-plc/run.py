#!/usr/bin/env python3
"""field-plc: the water and power soft-PLCs for Packet River.

  * water treatment + distribution  - Modbus/TCP, container port 502
  * power substation bus            - Modbus/TCP, container port 503
  * a shared operator HMI (Flask)   - port 8093

The physics live in simmap; these PLCs serve the field protocol, run a golden
control program, and - when the maintenance-mode coil is set - expose this
session's flag across an input-register block (IR 100+).

Deliberate weakness (MODBUS_WRITE_OPEN=1): coil and register writes are
accepted from any source with no validation. Stop the high-lift pump and the
town loses water; open a feeder breaker and a zone goes dark. Set to 0 (or run
the hardened topology) and the scan loop re-asserts the safe state every pass,
so the same writes get stomped.
"""
import os
import threading
import time

from pymodbus.server import StartTcpServer

import maps
from maps import FACTORY, POWER, WATER, FLAG_IR_BASE, FLAG_IR_LEN, pack_flag
from store import FCTX, FLOCK, PCTX, PLOCK, WCTX, WLOCK, rd, wr

WRITE_OPEN = os.environ.get("MODBUS_WRITE_OPEN", "1") == "1"
FLAG_DIR = "/run/secret"


def _read_flag(name: str) -> str:
    try:
        with open(f"{FLAG_DIR}/{name}/flag.txt") as f:
            return f.read().strip()
    except OSError:
        return f"PKTR{{{name}_flag_missing}}"


WATER_FLAG = _read_flag("water_modbus_pump")
POWER_FLAG = _read_flag("power_modbus_feeder")
FACTORY_FLAG = _read_flag("factory_modbus")


def seed() -> None:
    """Golden state: everything running, setpoints nominal."""
    wr(WCTX, WLOCK, 1, 0, [1, 1, 1, 1])            # INTAKE HIGHLIFT CHLORINE MAIN_VALVE
    wr(WCTX, WLOCK, 3, WATER["hr"]["HIGHLIFT_SP"], [WATER["golden"]["HIGHLIFT_SP"]])
    wr(WCTX, WLOCK, 3, WATER["hr"]["CHLORINE_SP"], [WATER["golden"]["CHLORINE_SP"]])
    wr(PCTX, PLOCK, 1, 0, [1, 1, 1, 1, 1, 1])      # BRK_MAIN + 4 feeders + GEN_ENABLE
    wr(PCTX, PLOCK, 3, POWER["hr"]["GEN_SP"], [POWER["golden"]["GEN_SP"]])
    wr(FCTX, FLOCK, 1, 0, [1, 0, 1, 0])            # LINE_RUN, ESTOP_BYPASS off, GANTRY, HOPPER_GATE closed
    wr(FCTX, FLOCK, 3, FACTORY["hr"]["LINE_SPEED"], [FACTORY["golden"]["LINE_SPEED"]])
    print(f"[field-plc] seeded golden state; WRITE_OPEN={WRITE_OPEN}")


def _clamp(ctx, lock, addr, lo, hi) -> None:
    v = rd(ctx, lock, 3, addr)[0]
    wr(ctx, lock, 3, addr, [max(lo, min(v, hi))])


def _flag_block(ctx, lock, maint_coil, flag) -> None:
    on = rd(ctx, lock, 1, maint_coil)[0]
    wr(ctx, lock, 4, FLAG_IR_BASE, pack_flag(flag) if on else [0] * FLAG_IR_LEN)


def scan_loop() -> None:
    while True:
        try:
            if not WRITE_OPEN:
                # hardened: re-assert the safe operating state every scan
                wr(WCTX, WLOCK, 1, 0, [1, 1, 1, 1])
                _clamp(WCTX, WLOCK, WATER["hr"]["HIGHLIFT_SP"], *WATER["sp_clamp"]["HIGHLIFT_SP"])
                _clamp(WCTX, WLOCK, WATER["hr"]["CHLORINE_SP"], *WATER["sp_clamp"]["CHLORINE_SP"])
                wr(PCTX, PLOCK, 1, 0, [1, 1, 1, 1, 1, 1])
                _clamp(PCTX, PLOCK, POWER["hr"]["GEN_SP"], *POWER["sp_clamp"]["GEN_SP"])
                wr(FCTX, FLOCK, 1, FACTORY["coil"]["LINE_RUN"], [1])
                wr(FCTX, FLOCK, 1, FACTORY["coil"]["ESTOP_BYPASS"], [0])
                wr(FCTX, FLOCK, 1, FACTORY["coil"]["HOPPER_GATE"], [0])
                _clamp(FCTX, FLOCK, FACTORY["hr"]["LINE_SPEED"], *FACTORY["sp_clamp"]["LINE_SPEED"])

            # alarms derived from the PVs simmap writes back
            wp = rd(WCTX, WLOCK, 3, WATER["hr"]["MAIN_PRESSURE"])[0] / 10.0
            wt = rd(WCTX, WLOCK, 3, WATER["hr"]["TANK_LEVEL"])[0] / 10.0
            wc = rd(WCTX, WLOCK, 3, WATER["hr"]["CHLORINE_RESIDUAL"])[0] / 100.0
            wr(WCTX, WLOCK, 2, WATER["di"]["LOW_PRESSURE"], [int(wp < 25)])
            wr(WCTX, WLOCK, 2, WATER["di"]["LOW_TANK"], [int(wt < 20)])
            wr(WCTX, WLOCK, 2, WATER["di"]["LOW_CHLORINE"], [int(wc < 0.3)])

            # factory: line jam if the e-stop is bypassed and the line is
            # running fast, or the hopper is dumping with no car in position
            fco = rd(FCTX, FLOCK, 1, 0, 8)
            fspd = rd(FCTX, FLOCK, 3, FACTORY["hr"]["LINE_SPEED"])[0]
            car = rd(FCTX, FLOCK, 2, FACTORY["di"]["CAR_IN_POSITION"])[0]
            jam = int((fco[FACTORY["coil"]["ESTOP_BYPASS"]] and fspd > 90)
                      or (fco[FACTORY["coil"]["HOPPER_GATE"]] and not car)
                      or not fco[FACTORY["coil"]["LINE_RUN"]])
            wr(FCTX, FLOCK, 2, FACTORY["di"]["LINE_JAM"], [jam])

            _flag_block(WCTX, WLOCK, WATER["coil"]["MAINT_MODE"], WATER_FLAG)
            _flag_block(PCTX, PLOCK, POWER["coil"]["MAINT_MODE"], POWER_FLAG)
            _flag_block(FCTX, FLOCK, FACTORY["coil"]["MAINT_MODE"], FACTORY_FLAG)
        except Exception as exc:  # keep the loop alive
            print("[field-plc] scan error:", exc)
        time.sleep(0.3)


def _serve(ctx, port) -> None:
    StartTcpServer(context=ctx, address=("0.0.0.0", port))


def main() -> None:
    seed()
    threading.Thread(target=_serve, args=(WCTX, 502), daemon=True).start()
    threading.Thread(target=_serve, args=(PCTX, 503), daemon=True).start()
    threading.Thread(target=_serve, args=(FCTX, 504), daemon=True).start()
    threading.Thread(target=scan_loop, daemon=True).start()
    import hmi
    hmi.app.run(host="0.0.0.0", port=8093, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
