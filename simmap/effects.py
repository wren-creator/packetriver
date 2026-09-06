"""EXPLOIT -> town mutation dispatch table.

Each entry sets an initial condition on the TownState; the physics in
`models/town.py` produce the visible consequence over the next few seconds.
In Phase 0 these are driven by debug buttons in the UI and by test messages
on pkt/score/events. From Phase 1 on, `scoring` publishes the real thing after
a valid flag submission.

Shape borrowed from zstack-monitor/server/rules/*.cjs: {id: fn(town, payload)}.
"""
from __future__ import annotations


def _shop(town, payload, status):
    key = payload.get("shop", "generalstore")
    for s in town.shops:
        if s.key == key:
            s.site_status = status
            return


def _bank_drain(town, payload):
    town.bank.site_status = "carded"
    town.bank.balance = 0
    town.bank.atm_drained = True
    town.bank.admin_pwned = True
    town.bank._alarm_cut = True


def _cityhall_deface(town, payload):
    town.cityhall.announcement_text = payload.get("text", "OWNED BY " + payload.get("player", "anon"))
    town.cityhall.site_status = "defaced"


EFFECTS = {
    # --- Main Street ---
    "shop_sqli_dump":  lambda town, p: _shop(town, p, "db_dumped"),
    "shop_xss_deface": lambda town, p: _shop(town, p, "defaced"),
    "shop_carded":     lambda town, p: _shop(town, p, "carded"),

    # --- Bank / civic ---
    "bank_drain":      _bank_drain,
    "cityhall_deface": _cityhall_deface,
    "cityhall_payroll": lambda town, p: (
        setattr(town.cityhall, "payroll_balance", 0),
        setattr(town.cityhall, "admin_pwned", True),
    ),
    "police_deface": lambda town, p: setattr(town.police, "site_status", "defaced"),
    "fire_deface":   lambda town, p: setattr(town.fire, "site_status", "defaced"),

    # --- utilities ---
    "water_main_break": lambda town, p: setattr(town.water, "broken", True),
    "sewage_bypass": lambda town, p: (
        setattr(town.sewage, "effluent_path", "raw"),
        setattr(town.sewage, "aeration_on", False),
    ),
    "power_trip_feeder": lambda town, p: town.power.feeders.__setitem__(
        p.get("feeder", "industrial"), False),

    # --- traffic + rail ---
    "traffic_all_green": lambda town, p: [
        setattr(x, "mode", "ALL-GREEN") for x in town.traffic
        if not p.get("intersection") or x.id == int(p["intersection"])
    ],
    "rail_switch_spur": lambda town, p: setattr(town.rail, "switch_position", "spur"),
}


def apply(town, effect_id: str, payload: dict | None = None) -> bool:
    fn = EFFECTS.get(effect_id)
    if not fn:
        return False
    fn(town, payload or {})
    return True
