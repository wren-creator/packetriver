"""Coarse widget-factory model - assembly line + train loading.

Driven from the `field-plc` factory PLC. Bypass the e-stop and overspeed the
line, or open the hopper gate with no rail car under it, and throughput
craters / the line jams.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FactoryModel:
    throughput_pct: float = 100.0
    cars_loaded: int = 3
    line_jam: bool = False
    estop_bypassed: bool = False
    hopper_open: bool = False
    line_running: bool = True
    _spill_t: float = 0.0

    def step(self, dt: float, *, line_run: bool, estop_bypass: bool,
             hopper_gate: bool, car_in_position: bool, line_speed: int,
             jam_di: bool) -> None:
        self.line_running = bool(line_run)
        self.estop_bypassed = bool(estop_bypass)
        self.hopper_open = bool(hopper_gate)
        self.line_jam = bool(jam_di)

        # target throughput: nominal when running clean, near zero on a jam or
        # a stopped line, reduced by an unsafe overspeed
        if self.line_jam or not line_run:
            target = 0.0
        elif estop_bypass and line_speed > 90:
            target = 45.0
        else:
            target = min(120.0, line_speed / 70.0 * 100.0)
        self.throughput_pct += (target - self.throughput_pct) * min(1.0, dt / 4.0)

        # product spilled onto the tracks if the hopper dumps with no car
        if hopper_gate and not car_in_position:
            self._spill_t += dt
        else:
            self._spill_t = max(0.0, self._spill_t - dt * 0.5)
