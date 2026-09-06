"""Coarse water treatment + distribution model.

simmap drives this from the `field-plc` water PLC each tick: it reads the pump
coils and setpoints, steps the model, and writes the resulting PVs (tower
level, main pressure, chlorine residual, flow) back so the HMI stays live.
Stop the high-lift pump over Modbus and the pressure bleeds to zero within a
few ticks; the town loses water.
"""
from __future__ import annotations

from dataclasses import dataclass

GOLDEN_PSI = 62.0


@dataclass
class WaterModel:
    tank_pct: float = 72.0
    pressure_psi: float = GOLDEN_PSI
    chlorine_ppm: float = 1.20
    flow_gpm: float = 470.0

    def step(self, dt: float, *, intake: bool, highlift: bool, chlorine: bool,
             main_valve: bool, sp_psi: float, sp_ppm: float) -> None:
        inflow = 520.0 if (intake and main_valve) else 0.0
        demand = 470.0
        self.tank_pct = max(0.0, min(100.0, self.tank_pct + (inflow - demand) * dt * 0.02))

        pumping = highlift and main_valve and self.tank_pct > 4.0
        target_p = sp_psi if pumping else 0.0
        self.pressure_psi += (target_p - self.pressure_psi) * min(1.0, dt / 4.0)

        target_cl = sp_ppm if (chlorine and pumping) else 0.0
        self.chlorine_ppm += (target_cl - self.chlorine_ppm) * min(1.0, dt / 6.0)

        self.flow_gpm = demand if self.pressure_psi > 15 else max(0.0, self.pressure_psi * 8)

    @property
    def pressure_pct(self) -> float:
        return max(0.0, min(120.0, self.pressure_psi / GOLDEN_PSI * 100.0))

    @property
    def houses_supplied(self) -> int:
        if self.pressure_psi > 25:
            return 12
        if self.pressure_psi > 12:
            return 6
        return 0

    @property
    def quality(self) -> str:
        if self.pressure_pct < 20:
            return "dry"
        if self.chlorine_ppm < 0.30 or self.pressure_pct < 70:
            return "brown"
        return "clean"
