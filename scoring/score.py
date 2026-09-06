"""The score formula.

points = round(base * (1 + stealth) * (1 + chain) * speed) - penalties

- stealth: +0.5 if the Alert Level did not rise between arming the technique and
  submitting the flag (Phase 4 wires the real alert; until then it's 0/0).
- chain:   +0.25 per prior distinct technique solved on the same subsystem this
  run, capped at +1.0.
- speed:   1.5 under T_FAST, ramping down to 1.0 by T_SLOW, 0.8 floor after.

The cascade kicker (+0.3 if a pkt/sim/physical/* event for this subsystem fired
within 20s of the submit) lands in Phase 4 with the physical events.
"""
from __future__ import annotations

T_FAST = 120.0
T_SLOW = 600.0


def compute(base: int, alert_at_arm: int, alert_at_submit: int,
            prior_on_subsystem: int, elapsed_s: float) -> tuple[int, dict]:
    stealth = 0.5 if alert_at_submit <= max(1, alert_at_arm) else 0.0
    chain = min(1.0, 0.25 * max(0, prior_on_subsystem))
    if elapsed_s <= T_FAST:
        speed = 1.5
    elif elapsed_s >= T_SLOW:
        speed = 0.8
    else:
        speed = 1.5 - 0.5 * (elapsed_s - T_FAST) / (T_SLOW - T_FAST)
    points = round(base * (1 + stealth) * (1 + chain) * speed)
    return points, {
        "base": base,
        "stealth": stealth,
        "chain": round(chain, 2),
        "speed": round(speed, 2),
        "elapsed_s": round(elapsed_s, 1),
    }
