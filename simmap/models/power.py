"""Coarse substation bus model.

simmap drives this from the `field-plc` power PLC each tick: it reads the
breaker coils and generation setpoint, steps the model, and writes the bus
frequency / voltage / load back. Open a feeder breaker over Modbus and that
zone goes dark; open the main and the whole town does, with the frequency
diving as the island collapses.
"""
from __future__ import annotations

from dataclasses import dataclass, field

FEEDERS = ["residential", "downtown", "industrial", "streetlights"]


@dataclass
class PowerModel:
    freq_hz: float = 60.0
    volt_kv: float = 13.8
    load_mw: float = 7.6
    feeders: dict = field(default_factory=lambda: {f: True for f in FEEDERS})

    def step(self, dt: float, *, main: bool, res: bool, downtown: bool,
             industrial: bool, streetlights: bool, gen: bool, sp_mw: float) -> None:
        self.feeders = {
            "residential": bool(res and main),
            "downtown": bool(downtown and main),
            "industrial": bool(industrial and main),
            "streetlights": bool(streetlights and main),
        }
        open_n = sum(1 for v in self.feeders.values() if not v)
        target_f = 60.0 - 0.7 * open_n
        if not main:
            target_f -= 3.5          # islanded, collapsing
        if not gen:
            target_f -= 1.0
        self.freq_hz += (target_f - self.freq_hz) * min(1.0, dt / 3.0)

        served = sum(1 for v in self.feeders.values() if v)
        self.load_mw = 1.9 * served
        self.volt_kv = 13.8 if main else 0.0
