"""Per-service front-door credentials (the ones that are NOT the scored bug).

The field-plc SCADA HMIs are protected by an operator login, but the scored
weakness there is the *unauthenticated* Modbus write that bypasses it. So the
HMI login is texture - and texture should follow good practice: one distinct
credential per plant, minted fresh each boot, rotatable on demand.

`scoring` owns the vault (it already has write access to the shared volume).
It writes one file per plant under /run/secret/creds/ ; field-plc reads its own
live on every request, so a rotation needs no restart. The blue team rotates
the whole set at Alert Level 2 by publishing pkt/creds/rotate.

The "credential IS the bug" logins (AS/400 QSECOFR, z16 IBMUSER, the shop
default creds) are deliberately static and are NOT managed here - a shipped
default that was never rotated is the whole lesson.
"""
from __future__ import annotations

import json
import pathlib
import secrets

CRED_DIR = pathlib.Path("/run/secret/creds")
PLANTS = ["water", "power", "factory", "sewage"]

# readable but not guessable: two words + two digits, e.g. "amber-relay-47"
_WORDS = ("amber alloy basin beacon cedar cobalt delta ember ferro granite "
          "harbor indigo juniper kelvin lumen maple nickel onyx piston quartz "
          "raven signal tundra umbra vector willow xenon yarrow zephyr").split()


def _mint() -> str:
    return f"{secrets.choice(_WORDS)}-{secrets.choice(_WORDS)}-{secrets.randbelow(90) + 10}"


def generate() -> None:
    CRED_DIR.mkdir(parents=True, exist_ok=True)
    for p in PLANTS:
        (CRED_DIR / f"hmi-{p}.json").write_text(
            json.dumps({"user": f"op.{p}", "pass": _mint()}) + "\n")
    _write_handover()
    print(f"[creds] minted {len(PLANTS)} field-HMI credentials -> {CRED_DIR}")


def _write_handover() -> None:
    """The 'shift handover' sheet an ops team would leave on the historian.
    field-plc serves this unauthenticated at /ops/handover.txt - so the current
    set is discoverable, and it always reflects the latest rotation."""
    lines = ["PACKET RIVER FIELD OPERATIONS - SHIFT HANDOVER",
             "operator terminal access  (rotate per policy - do not distribute)",
             "-" * 52]
    for p in PLANTS:
        try:
            c = json.loads((CRED_DIR / f"hmi-{p}.json").read_text())
            lines.append(f"  {p.capitalize():9}  {c['user']} / {c['pass']}")
        except OSError:
            pass
    (CRED_DIR / "handover.txt").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    generate()
