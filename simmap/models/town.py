"""The Packet River town state model.

One @dataclass per subsystem, plain floats and bools, golden defaults. `step`
is a coarse first-order-lag integrator so a breach has a visible consequence
within a tick or two. Phase 0 carries a light idle model plus a debug
breach/reset path; later phases fold in the physics from crosscreek/process-sim
and drive `apply_effect` from real flag submissions on pkt/score/events.
"""
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass, field

# One full auto cycle: a long green each way, a short all-red between. On the
# map each crossroads is a single signal dot, so it sits green most of the
# time and blinks red briefly on the changeover - until it is hijacked to
# ALL-GREEN.
TRAFFIC_CYCLE = [("ns-green", 6.0), ("all-red", 2.0), ("ew-green", 6.0), ("all-red", 2.0)]

# The train runs the visible top track (train_pos 0..1), then spends the rest
# of the cycle off-screen before re-entering from the start.
TRAIN_CYCLE = 1.7
# Where the spur branches, as a fraction of the visible run. Tuned to the
# overlay's spurPath[0] (under the "R" of "Main Rail Line" on the base art) so
# the train hands off to the spur polyline with no visible jump.
SWITCH_POINT = 0.256
# The spur is a short leg; the train covers it in ~4-5 s (roughly the same
# on-screen speed as the main line) before it piles into the plant.
SPUR_SPEED = 6.0

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
    ["all", "traffic", "rail", "factory", "water", "sewage", "power",
     "cityhall", "bank", "police", "fire", "events"]
    + [k for k, _ in SHOPS]
)

# --- timed events -----------------------------------------------------
# PKT_EVENTS: off | calm (default) | lively. The gap between events is drawn
# uniformly from the band; each event runs for a fixed window.
EVENT_MODE = os.environ.get("PKT_EVENTS", "calm").lower()
EVENT_BANDS = {"calm": (300.0, 540.0), "lively": (120.0, 260.0)}
EVENT_DURATION = {"news_crew": 90.0, "inspector": 75.0, "parade": 60.0}
EVENT_NAMES = ("news_crew", "inspector", "parade")


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
    on_spur: bool = False           # train has been routed onto the spur
    spur_pos: float = 0.0           # 0..1 progress down the spur toward the plant
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
    treatment_pct: float = 96.0
    turbidity_ntu: float = 3.0
    river_contamination: float = 0.0
    swimmers_sick: bool = False


@dataclass
class Factory:
    throughput_pct: float = 100.0
    line_running: bool = True
    line_jam: bool = False
    estop_bypassed: bool = False
    hopper_open: bool = False
    on_fire: bool = False           # set by a rail derail into the factory


@dataclass
class Power:
    bus_freq_hz: float = 60.0
    feeders: dict = field(default_factory=lambda: {
        "residential": True,
        "business": True,
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
    blue_actions: list = field(default_factory=list)   # SOC responses, newest last


@dataclass
class Events:
    """Scheduled goings-on that make the town feel lived-in and raise the
    stakes. `clock` is seconds since this Events object was created."""
    clock: float = 0.0
    news_crew: bool = False
    inspector: bool = False
    parade: bool = False
    news_focus: str | None = None       # building the van is parked at
    _ends: dict = field(default_factory=dict)      # name -> clock time it ends
    _next: dict = field(default_factory=dict)      # name -> clock time it fires
    _unsafe_at_arrival: bool = False              # inspector: was anything bad?
    log: list = field(default_factory=list)        # recent "what happened", newest last
    pending: list = field(default_factory=list)    # drained by wsgi -> pkt/sim/event/*

    def __post_init__(self):
        if EVENT_MODE in EVENT_BANDS:
            lo, hi = EVENT_BANDS[EVENT_MODE]
            # stagger the first occurrences so they don't all fire together
            for i, name in enumerate(EVENT_NAMES):
                self._next[name] = random.uniform(lo, hi) * (0.4 + 0.5 * i)


# (rise_at, level). Falling back a level needs heat below the NEXT band's rise
# point minus a margin, so the meter does not flap around a threshold.
ALERT_THRESHOLDS = [(150, 5), (110, 4), (75, 3), (45, 2), (20, 1)]
ALERT_HYSTERESIS = 8.0


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
            # stagger the corners so they don't all blink red at the same instant
            self.traffic = []
            for i in range(1, 6):
                x = Intersection(id=i)
                x._phase_i = (i - 1) % len(TRAFFIC_CYCLE)
                x._t = ((i - 1) * 1.7) % TRAFFIC_CYCLE[x._phase_i][1]
                self.traffic.append(x)
        if s in ("all", "rail"):
            self.rail = Rail()
        if s in ("all", "factory"):
            self.factory = Factory()
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
        if s in ("all", "events"):
            self.events = Events()

    # -- tick ----------------------------------------------------------
    def step(self, dt: float) -> None:
        self._step_events(dt)
        self._step_traffic(dt)
        self._step_rail(dt)
        self._step_water(dt)
        self._step_sewage(dt)
        self._step_power(dt)
        self._step_bank()
        self._step_alert(dt)
        self.state_seq += 1

    # -- timed events --------------------------------------------------
    def _worst_subsystem(self) -> str | None:
        """The single most-damaged thing right now, or None if all is well."""
        if getattr(self.rail, "derailed", False):
            return "rail"
        if self.factory.on_fire:
            return "factory"
        if self.sewage.effluent_path == "raw":
            return "sewage"
        if not all(self.power.feeders.values()):
            return "power"
        if self.water.quality == "dry":
            return "water"
        if any(x.mode == "ALL-GREEN" for x in self.traffic):
            return "traffic"
        for s in self.shops:
            if s.site_status != "healthy":
                return s.key
        if self.bank.site_status != "healthy":
            return "bank"
        if self.cityhall.site_status != "healthy" or self.cityhall.admin_pwned:
            return "cityhall"
        return None

    def event_heat_mult(self, subsystem: str | None) -> float:
        """Extra Alert heat while a news crew is filming the affected system."""
        ev = self.events
        if ev.news_crew and subsystem and subsystem == ev.news_focus:
            return 1.6
        return 1.0

    def _step_events(self, dt: float) -> None:
        ev = self.events
        if EVENT_MODE not in EVENT_BANDS:
            return
        ev.clock += dt
        lo, hi = EVENT_BANDS[EVENT_MODE]
        for name in EVENT_NAMES:
            if not getattr(ev, name):
                if ev._next.get(name, 1e18) <= ev.clock:
                    setattr(ev, name, True)
                    ev._ends[name] = ev.clock + EVENT_DURATION[name]
                    if name == "news_crew":
                        ev.news_focus = self._worst_subsystem() or "cityhall"
                    elif name == "inspector":
                        ev._unsafe_at_arrival = self._worst_subsystem() is not None
                    ev.log.append(f"{int(ev.clock)}s  {name.replace('_', ' ')} arrived")
                    ev.log[:] = ev.log[-6:]
                    ev.pending.append({"name": name, "phase": "start",
                                       "focus": ev.news_focus})
                continue
            if ev.clock >= ev._ends.get(name, 0.0):
                setattr(ev, name, False)
                note = f"{name.replace('_', ' ')} ended"
                if name == "news_crew":
                    ev.news_focus = None
                elif name == "inspector":
                    still_bad = self._worst_subsystem()
                    if still_bad and not ev._unsafe_at_arrival:
                        self.add_heat(45)
                        self.note_blue_action(
                            "Inspector on site during an active incident - citation issued")
                        note = "inspector cited an active incident (+heat)"
                    elif still_bad:
                        self.add_heat(20)
                        note = "inspector left; findings noted"
                    else:
                        note = "inspector left; all clear"
                ev.log.append(f"{int(ev.clock)}s  {note}")
                ev.log[:] = ev.log[-6:]
                ev.pending.append({"name": name, "phase": "end"})
                ev._next[name] = ev.clock + random.uniform(lo, hi)

    def _step_traffic(self, dt: float) -> None:
        business_up = self.power.feeders["business"]
        # a hijacked signal during the parade racks up crashes twice as fast
        crash_period = 1.5 if self.events.parade else 3.0
        for x in self.traffic:
            if not business_up:
                x.phase = "dark"
                continue
            if x.mode == "ALL-GREEN":
                x.phase = "ALL-GREEN"
                x._crash_t += dt
                if x._crash_t >= crash_period:
                    x._crash_t = 0.0
                    x.crash_count += 2 if self.events.parade else 1
                continue
            x.mode = "auto"
            x._t += dt
            if x._t >= TRAFFIC_CYCLE[x._phase_i][1]:
                x._t = 0.0
                x._phase_i = (x._phase_i + 1) % len(TRAFFIC_CYCLE)
            x.phase = TRAFFIC_CYCLE[x._phase_i][0]

    def _step_rail(self, dt: float) -> None:
        r = self.rail
        if r.derailed:
            return
        # already committed to the spur: run down it toward the plant, then
        # pile into the factory at the end
        if r.on_spur:
            r.spur_pos = min(1.0, r.spur_pos + r.train_speed * SPUR_SPEED * dt)
            if r.spur_pos >= 1.0:
                r.derailed = True
                r.factory_fire = True
                self.factory.on_fire = True
                r.train_speed = 0.0
                # a loading car in the way turns a derail into a pile-up: the
                # line is buried, not just stopped
                if self.factory.hopper_open:
                    self.factory.throughput_pct = 0.0
                    self.factory.line_jam = True
            return
        prev = r.train_pos
        r.train_pos += r.train_speed * dt
        if r.train_pos >= TRAIN_CYCLE:
            r.train_pos -= TRAIN_CYCLE
        # crossed the switch point on this pass across the visible run
        crossed = prev < SWITCH_POINT <= r.train_pos
        if r.switch_position == "spur" and crossed:
            r.on_spur = True
            r.train_pos = SWITCH_POINT   # pin at the branch; the spur takes over

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
        # the plant state (effluent_path, aeration) comes from the PLC loop when
        # "sewage" is external; the river plume physics run here regardless.
        sg = self.sewage
        if "sewage" not in self.external:
            sg.effluent_path = "raw" if not sg.aeration_on else "treated"
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
        self.bank.alarm_armed = self.power.feeders["business"] and not self.bank._alarm_cut

    def _step_alert(self, dt: float) -> None:
        a = self.alert
        a.heat *= 0.5 ** (dt / 120.0)          # ~2 min half-life leaky bucket
        target = 0
        for thresh, lvl in ALERT_THRESHOLDS:
            if a.heat >= thresh:
                target = lvl
                break
        if target > a.level:
            a.level = target                   # rise immediately
        elif target < a.level:
            # only fall a level once heat is clearly below that level's rise point
            rise_at = next(t for t, lv in ALERT_THRESHOLDS if lv == a.level)
            if a.heat < rise_at - ALERT_HYSTERESIS:
                a.level = target

    def add_heat(self, amount: float) -> None:
        self.alert.heat += amount

    def note_blue_action(self, text: str) -> None:
        self.alert.blue_actions.append(text)
        self.alert.blue_actions[:] = self.alert.blue_actions[-6:]

    # -- snapshot ----------------------------------------------------
    def snapshot(self) -> dict:
        w, p = self.water, self.power
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
                "on_spur": self.rail.on_spur,
                "spur_pos": round(self.rail.spur_pos, 4),
                "derailed": self.rail.derailed,
                "console_locked": self.rail.console_locked,
                "factory_fire": self.rail.factory_fire,
            },
            "factory": {
                "throughput_pct": round(self.factory.throughput_pct, 1),
                "line_running": self.factory.line_running,
                "line_jam": self.factory.line_jam,
                "estop_bypassed": self.factory.estop_bypassed,
                "hopper_open": self.factory.hopper_open,
                "on_fire": self.factory.on_fire or self.rail.factory_fire,
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
                "treatment_pct": round(self.sewage.treatment_pct, 1),
                "turbidity_ntu": round(self.sewage.turbidity_ntu, 1),
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
            "alert": {
                "level": self.alert.level,
                "heat": round(self.alert.heat, 1),
                "blue_actions": list(self.alert.blue_actions),
            },
            "events": {
                "mode": EVENT_MODE,
                "clock": int(self.events.clock),
                "news_crew": self.events.news_crew,
                "inspector": self.events.inspector,
                "parade": self.events.parade,
                "news_focus": self.events.news_focus,
                "log": list(self.events.log),
            },
        }
