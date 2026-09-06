"""The Packet River town state model.

One @dataclass per subsystem, plain floats and bools, golden defaults. `step`
is a coarse first-order-lag integrator so a breach has a visible consequence
within a tick or two. Phase 0 carries a light idle model plus a debug
breach/reset path; later phases fold in the physics from crosscreek/process-sim
and drive `apply_effect` from real flag submissions on pkt/score/events.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

# One full auto cycle, ~4s per entry.
TRAFFIC_CYCLE = ["ns-green", "all-red", "ew-green", "all-red"]
PHASE_SECONDS = 4.0

# The train runs the visible top track (train_pos 0..1), then spends the rest
# of the cycle off-screen before re-entering from the start.
TRAIN_CYCLE = 1.7
SWITCH_POINT = 0.42   # where the spur branches, as a fraction of the visible run

# The eight Main Street storefronts. The bank, police, and fire are their own
# first-class entities; the cinema and bakery are set dressing (not modelled).
SHOPS = [
    ("generalstore", "General Store"),
    ("hardware", "Hardware & Supply"),
    ("pharmacy", "Pharmacy / Apothecary"),
    ("diner", "Local Diner / Cafe"),
    ("barber", "Barbershop / Salon"),
    ("tavern", "Tavern / Watering Hole"),
    ("drycleaner", "Dry Cleaners / Laundromat"),
    ("baittackle", "Bait & Tackle / Beach Outfitter"),
]

RESET_SCOPES = (
    ["all", "traffic", "rail", "water", "sewage", "power", "cityhall", "bank", "police", "fire"]
    + [k for k, _ in SHOPS]
)


@dataclass
class Intersection:
    id: int
    phase: str = "ns-green"
    mode: str = "auto"          # auto | ALL-GREEN | dark
    crash_count: int = 0
    _t: float = 0.0
    _phase_i: int = 0
    _crash_t: float = 0.0


@dataclass
class Rail:
    train_pos: float = 0.0
    train_speed: float = 0.035
    switch_position: str = "loop"   # loop | spur
    derailed: bool = False
    console_locked: bool = True
    factory_fire: bool = False


@dataclass
class Water:
    tank_pct: float = 78.0
    mains_pressure_pct: float = 100.0
    quality: str = "clean"          # clean | brown | dry
    houses_supplied: int = 12
    broken: bool = False            # pressure lost; kept for the map + effects


@dataclass
class Sewage:
    effluent_path: str = "treated"  # treated | raw
    aeration_on: bool = True
    river_contamination: float = 0.0
    swimmers_sick: bool = False


@dataclass
class Power:
    bus_freq_hz: float = 60.0
    feeders: dict = field(default_factory=lambda: {
        "residential": True,
        "downtown": True,
        "streetlights": True,
        "industrial": True,
    })


@dataclass
class Shop:
    key: str
    name: str
    site_status: str = "healthy"     # healthy | defaced | db_dumped | carded
    fraud_charges: int = 0


@dataclass
class Bank:
    site_status: str = "healthy"
    balance: int = 2_400_000
    alarm_armed: bool = True
    atm_drained: bool = False
    admin_pwned: bool = False
    _alarm_cut: bool = False


@dataclass
class Civic:
    name: str
    site_status: str = "healthy"
    dispatch_pwned: bool = False


@dataclass
class CityHall:
    site_status: str = "healthy"
    payroll_balance: int = 480_000
    announcement_text: str = "Welcome to Packet River. Founder's Day is Saturday."
    admin_pwned: bool = False


@dataclass
class Alert:
    level: int = 0
    heat: float = 0.0


ALERT_THRESHOLDS = [(150, 5), (110, 4), (75, 3), (45, 2), (20, 1)]


class TownState:
    def __init__(self):
        self.state_seq = 0
        # subsystems driven by an external client loop (icsloops) instead of the
        # built-in idle physics; their _step_* methods no-op when listed here.
        self.external: set[str] = set()
        self.reset("all")

    # -- reset -----------------------------------------------------------
    def reset(self, scope: str = "all") -> None:
        s = scope
        if s in ("all", "traffic"):
            self.traffic = [Intersection(id=i) for i in range(1, 5)]
        if s in ("all", "rail"):
            self.rail = Rail()
        if s in ("all", "water"):
            self.water = Water()
        if s in ("all", "sewage"):
            self.sewage = Sewage()
        if s in ("all", "power"):
            self.power = Power()
        if s == "all":
            self.shops = [Shop(key=k, name=n) for k, n in SHOPS]
        else:
            for i, (k, n) in enumerate(SHOPS):
                if s == k:
                    self.shops[i] = Shop(key=k, name=n)
        if s in ("all", "bank"):
            self.bank = Bank()
        if s in ("all", "police"):
            self.police = Civic(name="Police Station")
        if s in ("all", "fire"):
            self.fire = Civic(name="Fire Department")
        if s in ("all", "cityhall"):
            self.cityhall = CityHall()
        if s == "all":
            self.alert = Alert()

    # -- tick ----------------------------------------------------------
    def step(self, dt: float) -> None:
        self._step_traffic(dt)
        self._step_rail(dt)
        self._step_water(dt)
        self._step_sewage(dt)
        self._step_power(dt)
        self._step_bank()
        self._step_alert(dt)
        self.state_seq += 1

    def _step_traffic(self, dt: float) -> None:
        downtown_up = self.power.feeders["downtown"]
        for x in self.traffic:
            if not downtown_up:
                x.phase = "dark"
                continue
            if x.mode == "ALL-GREEN":
                x.phase = "ALL-GREEN"
                x._crash_t += dt
                if x._crash_t >= 3.0:
                    x._crash_t = 0.0
                    x.crash_count += 1
                continue
            x.mode = "auto"
            x._t += dt
            if x._t >= PHASE_SECONDS:
                x._t = 0.0
                x._phase_i = (x._phase_i + 1) % len(TRAFFIC_CYCLE)
            x.phase = TRAFFIC_CYCLE[x._phase_i]

    def _step_rail(self, dt: float) -> None:
        r = self.rail
        if r.derailed:
            return
        prev = r.train_pos
        r.train_pos += r.train_speed * dt
        if r.train_pos >= TRAIN_CYCLE:
            r.train_pos -= TRAIN_CYCLE
        # crossed the switch point on this pass across the visible run
        crossed = prev < SWITCH_POINT <= r.train_pos
        if r.switch_position == "spur" and crossed:
            r.derailed = True
            r.factory_fire = True
            r.train_speed = 0.0

    def _step_water(self, dt: float) -> None:
        if "water" in self.external:
            return
        w = self.water
        if w.broken:
            w.mains_pressure_pct = max(0.0, w.mains_pressure_pct - 8.0 * dt)
            w.tank_pct = max(0.0, w.tank_pct - 2.0 * dt)
        else:
            w.mains_pressure_pct = min(100.0, w.mains_pressure_pct + 6.0 * dt)
            w.tank_pct = min(78.0, w.tank_pct + 1.5 * dt)
        w.quality = "dry" if w.mains_pressure_pct < 20 else \
            "brown" if w.mains_pressure_pct < 70 else "clean"

    def _step_sewage(self, dt: float) -> None:
        sg = self.sewage
        if sg.effluent_path == "raw":
            sg.river_contamination = min(1.0, sg.river_contamination + 0.04 * dt)
        else:
            sg.river_contamination = max(0.0, sg.river_contamination - 0.012 * dt)
        sg.swimmers_sick = sg.river_contamination > 0.45

    def _step_power(self, dt: float) -> None:
        if "power" in self.external:
            return
        p = self.power
        open_feeders = sum(1 for up in p.feeders.values() if not up)
        target = 60.0 - 0.7 * open_feeders
        p.bus_freq_hz += (target - p.bus_freq_hz) * min(1.0, dt / 3.0)

    def _step_bank(self) -> None:
        # Alarm is armed only while the industrial feeder is up and nobody has
        # cut it via the alarm panel.
        self.bank.alarm_armed = self.power.feeders["industrial"] and not self.bank._alarm_cut

    def _step_alert(self, dt: float) -> None:
        a = self.alert
        a.heat *= 0.5 ** (dt / 120.0)
        a.level = 0
        for thresh, lvl in ALERT_THRESHOLDS:
            if a.heat >= thresh:
                a.level = lvl
                break

    def add_heat(self, amount: float) -> None:
        self.alert.heat += amount

    # -- snapshot ----------------------------------------------------
    def snapshot(self) -> dict:
        w, p = self.water, self.power
        houses = [
            {"id": i, "has_water": w.mains_pressure_pct > 25, "has_power": p.feeders["residential"]}
            for i in range(1, 9)
        ]
        return {
            "state_seq": self.state_seq,
            "generated_at": time.time(),
            "traffic": [
                {"id": x.id, "phase": x.phase, "mode": x.mode, "crash_count": x.crash_count}
                for x in self.traffic
            ],
            "rail": {
                "train_pos": round(self.rail.train_pos, 4),
                "on_screen": self.rail.train_pos < 1.0,
                "switch_position": self.rail.switch_position,
                "derailed": self.rail.derailed,
                "console_locked": self.rail.console_locked,
                "factory_fire": self.rail.factory_fire,
            },
            "water": {
                "tank_pct": round(w.tank_pct, 1),
                "mains_pressure_pct": round(w.mains_pressure_pct, 1),
                "quality": w.quality,
                "houses_supplied": w.houses_supplied,
            },
            "sewage": {
                "effluent_path": self.sewage.effluent_path,
                "aeration_on": self.sewage.aeration_on,
                "river_contamination": round(self.sewage.river_contamination, 3),
                "swimmers_sick": self.sewage.swimmers_sick,
            },
            "power": {
                "bus_freq_hz": round(p.bus_freq_hz, 2),
                "feeders": dict(p.feeders),
                "streetlights_on": p.feeders["streetlights"],
            },
            "shops": [
                {"key": s.key, "name": s.name, "site_status": s.site_status,
                 "fraud_charges": s.fraud_charges}
                for s in self.shops
            ],
            "bank": {
                "site_status": self.bank.site_status,
                "balance": self.bank.balance,
                "alarm_armed": self.bank.alarm_armed,
                "atm_drained": self.bank.atm_drained,
                "admin_pwned": self.bank.admin_pwned,
            },
            "cityhall": {
                "site_status": self.cityhall.site_status,
                "payroll_balance": self.cityhall.payroll_balance,
                "announcement_text": self.cityhall.announcement_text,
                "admin_pwned": self.cityhall.admin_pwned,
            },
            "police": {"site_status": self.police.site_status, "dispatch_pwned": self.police.dispatch_pwned},
            "fire": {"site_status": self.fire.site_status, "dispatch_pwned": self.fire.dispatch_pwned},
            "houses": houses,
            "alert": {"level": self.alert.level, "heat": round(self.alert.heat, 1)},
        }
