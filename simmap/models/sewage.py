"""Coarse sewage treatment + treated-return model.

simmap drives this from the `field-plc` sewage PLC each tick: read the aeration
/ dosing / return-pump / bypass coils, step the model, write the PVs (dissolved
oxygen, turbidity, effluent quality, flow) back so the HMI stays live. Open the
storm bypass over Modbus - or stop aeration and dosing - and within a few ticks
the effluent runs raw to the outfall; the plume then spreads down to the beach.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SewageModel:
    do_mgl: float = 6.5          # dissolved oxygen in the aeration basin
    turbidity_ntu: float = 3.0
    quality_pct: float = 96.0    # effluent quality index
    flow_mgd: float = 4.2

    def step(self, dt: float, *, aeration: bool, chem_dose: bool,
             return_pump: bool, bypass_gate: bool, sp_mgl: float) -> None:
        # aeration holds dissolved oxygen up; without it the basin goes septic
        target_do = 6.8 if aeration else 0.5
        self.do_mgl += (target_do - self.do_mgl) * min(1.0, dt / 5.0)

        # treatment only works with aeration + dosing + a clear return path
        treating = aeration and chem_dose and return_pump and not bypass_gate
        target_turb = 2.5 if treating else 55.0
        self.turbidity_ntu += (target_turb - self.turbidity_ntu) * min(1.0, dt / 4.0)

        target_q = 96.0 if treating else 12.0
        self.quality_pct += (target_q - self.quality_pct) * min(1.0, dt / 4.0)

        self.flow_mgd = 0.6 if bypass_gate else (4.2 if return_pump else 1.0)

    @property
    def effluent_path(self) -> str:
        return "treated" if self.quality_pct > 55 else "raw"
