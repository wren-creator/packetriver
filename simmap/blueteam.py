"""Blue-team response to the Alert Level.

Called from the tick loop whenever the Alert Level rises. Each step is
observable in the snapshot (`alert.blue_actions`) and on `pkt/alert/action`;
a couple of them actually bite:

  L1  SOC investigating (banner only)
  L2  default credentials rotated  - traffic-plc + rail-plc get a fresh PIN /
      password over pkt/reset {scope:"creds"}, so an in-progress attacker's
      next canned command fails
  L3  rate limiting engaged (banner; the segmented build wires nginx limit_req)
  L4  OT segmentation engaged (banner; the segmented build drops the routes)
  L5  auto golden-restore of the most-damaged subsystem
"""
from __future__ import annotations

ACTIONS = {
    1: "SOC investigating - elevated scan and reject activity",
    2: "Default credentials rotated on the field controllers",
    3: "Rate limiting engaged on the web front doors",
    4: "OT network segmentation engaged - field bus isolated",
    5: "Automatic golden-restore of the worst-hit subsystem",
}


def _worst_scope(town) -> str | None:
    """Pick the single most-damaged subsystem for the L5 auto-restore."""
    if getattr(town.rail, "derailed", False) or town.factory.on_fire:
        return "rail" if town.rail.derailed else "factory"
    if town.sewage.effluent_path == "raw":
        return "sewage"
    if not all(town.power.feeders.values()):
        return "power"
    if town.water.quality == "dry":
        return "water"
    if any(x.mode == "ALL-GREEN" for x in town.traffic):
        return "traffic"
    for s in town.shops:
        if s.site_status != "healthy":
            return s.key
    if town.bank.site_status != "healthy":
        return "bank"
    return None


def respond(town, level: int, publish) -> None:
    """town is already locked by the caller. `publish(topic, payload_str)`."""
    action = ACTIONS.get(level)
    if not action:
        return
    town.note_blue_action(f"L{level}: {action}")
    publish("pkt/alert/action", f'{{"level": {level}, "action": "{action}"}}')

    if level == 2:
        publish("pkt/reset", '{"scope": "creds"}')
    elif level == 5:
        scope = _worst_scope(town)
        if scope:
            town.reset(scope)
            town.note_blue_action(f"L5: restored {scope} to golden state")
            try:
                import icsloops
                {"water": icsloops.restore_water, "power": icsloops.restore_power,
                 "factory": icsloops.restore_factory,
                 "sewage": icsloops.restore_sewage}.get(scope, lambda: None)()
            except Exception as exc:
                print("[blueteam] restore poke:", exc)
            publish("pkt/reset", f'{{"scope": "{scope}"}}')
