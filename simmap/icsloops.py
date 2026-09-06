"""Modbus client loops that drive the water + power physics from field-plc.

One thread per plant: read the PLC's coils and setpoints, step the model, write
the PVs back, and mirror the derived state into the shared TownState. Also
exposes the pokes the debug menu and pkt/reset use, so the debug buttons and a
real Modbus attack do the exact same thing.

Register offsets here must match field-plc/maps.py.
"""
from __future__ import annotations

import os
import threading
import time

from pymodbus.client import ModbusTcpClient

from models.power import PowerModel
from models.water import WaterModel

FIELD_HOST = os.environ.get("FIELD_PLC_HOST", "field-plc")
WATER_PORT, POWER_PORT = 502, 503
TICK = float(os.environ.get("TICK_SECONDS", "1.0"))

W = dict(INTAKE=0, HIGHLIFT=1, CHLORINE=2, MAIN_VALVE=3, MAINT=8,
         HIGHLIFT_SP=0, CHLORINE_SP=1, TANK=10, PRESS=11, CL=12, FLOW=13)
P = dict(MAIN=0, RES=1, BIZ=2, IND=3, ST=4, GEN=5, MAINT=8,
         GEN_SP=0, FREQ=10, VOLT=11, LOAD=12)
FEEDER_COIL = {"residential": P["RES"], "business": P["BIZ"],
               "industrial": P["IND"], "streetlights": P["ST"]}
WATER_GOLDEN_SP = (620, 120)   # high-lift psi x10, chlorine ppm x100
POWER_GOLDEN_SP = 80           # generation MW x10

_wc: ModbusTcpClient | None = None
_pc: ModbusTcpClient | None = None
_io_lock = threading.Lock()    # serialise writes we issue from effects/reset


def _conn(port: int) -> ModbusTcpClient:
    c = ModbusTcpClient(FIELD_HOST, port=port, timeout=2)
    c.connect()
    return c


# -- the loops --------------------------------------------------------
def _water_loop(town, lock) -> None:
    global _wc
    _wc = _conn(WATER_PORT)
    model = WaterModel()
    while True:
        t0 = time.time()
        try:
            if not _wc.connected:
                _wc.connect()
            with _io_lock:
                co = _wc.read_coils(0, 12, slave=1).bits
                hr = _wc.read_holding_registers(0, 16, slave=1).registers
            model.step(
                TICK,
                intake=bool(co[W["INTAKE"]]), highlift=bool(co[W["HIGHLIFT"]]),
                chlorine=bool(co[W["CHLORINE"]]), main_valve=bool(co[W["MAIN_VALVE"]]),
                sp_psi=hr[W["HIGHLIFT_SP"]] / 10.0, sp_ppm=hr[W["CHLORINE_SP"]] / 100.0,
            )
            with _io_lock:
                _wc.write_registers(W["TANK"], [
                    int(model.tank_pct * 10), int(model.pressure_psi * 10),
                    int(model.chlorine_ppm * 100), int(model.flow_gpm),
                ], slave=1)
            with lock:
                town.water.mains_pressure_pct = round(model.pressure_pct, 1)
                town.water.tank_pct = round(model.tank_pct, 1)
                town.water.quality = model.quality
                town.water.houses_supplied = model.houses_supplied
                town.water.broken = model.pressure_psi < 20
        except Exception as exc:
            print("[icsloops] water:", exc)
        time.sleep(max(0.0, TICK - (time.time() - t0)))


def _power_loop(town, lock) -> None:
    global _pc
    _pc = _conn(POWER_PORT)
    model = PowerModel()
    while True:
        t0 = time.time()
        try:
            if not _pc.connected:
                _pc.connect()
            with _io_lock:
                co = _pc.read_coils(0, 12, slave=1).bits
                hr = _pc.read_holding_registers(0, 16, slave=1).registers
            model.step(
                TICK,
                main=bool(co[P["MAIN"]]), res=bool(co[P["RES"]]),
                business=bool(co[P["BIZ"]]), industrial=bool(co[P["IND"]]),
                streetlights=bool(co[P["ST"]]), gen=bool(co[P["GEN"]]),
                sp_mw=hr[P["GEN_SP"]] / 10.0,
            )
            with _io_lock:
                _pc.write_registers(P["FREQ"], [
                    int(model.freq_hz * 100), int(model.volt_kv * 10),
                    int(model.load_mw * 10),
                ], slave=1)
            with lock:
                town.power.feeders = dict(model.feeders)
                town.power.bus_freq_hz = round(model.freq_hz, 2)
        except Exception as exc:
            print("[icsloops] power:", exc)
        time.sleep(max(0.0, TICK - (time.time() - t0)))


def start(town, lock) -> None:
    threading.Thread(target=_water_loop, args=(town, lock), daemon=True).start()
    threading.Thread(target=_power_loop, args=(town, lock), daemon=True).start()


# -- pokes (debug menu + pkt/reset) ----------------------------------
def _w(coil, val):
    if _wc:
        with _io_lock:
            _wc.write_coil(coil, bool(val), slave=1)


def _p(coil, val):
    if _pc:
        with _io_lock:
            _pc.write_coil(coil, bool(val), slave=1)


def stop_highlift():
    _w(W["HIGHLIFT"], False)


def trip_feeder(name: str):
    _p(FEEDER_COIL.get(name, P["IND"]), False)


def trip_main():
    _p(P["MAIN"], False)


def restore_water():
    if not _wc:
        return
    with _io_lock:
        _wc.write_coils(0, [True, True, True, True], slave=1)
        _wc.write_registers(W["HIGHLIFT_SP"], list(WATER_GOLDEN_SP), slave=1)
        _wc.write_coil(W["MAINT"], False, slave=1)


def restore_power():
    if not _pc:
        return
    with _io_lock:
        _pc.write_coils(0, [True, True, True, True, True, True], slave=1)
        _pc.write_registers(P["GEN_SP"], [POWER_GOLDEN_SP], slave=1)
        _pc.write_coil(P["MAINT"], False, slave=1)
