"""Per-session flag generation.

Runs once at container start, before the targets open for business. For each
technique it mints a random `PKTR{...}` flag, records the authoritative
technique -> (flag, effect, points) map in scoring.db, and drops the flag onto
the shared `pkt-flags` volume where the owning target's own entrypoint reads it
and plants it inside the vulnerable resource.

The flag string is the only currency: it exists only here and inside the one
target that owns it, never in simmap, the browser, or the player box.
"""
from __future__ import annotations

import pathlib
import secrets
import sqlite3

SECRET_DIR = pathlib.Path("/run/secret")
DB_PATH = pathlib.Path("/data/scoring.db")
SCHEMA = pathlib.Path(__file__).with_name("schema.sql")

# technique_id -> definition. `effect` is the effects.py key simmap applies when
# a valid flag for this technique is submitted.
TECHNIQUES = {
    "generalstore_sqli": {
        "subsystem": "shop",
        "target": "generalstore",
        "effect": "shop_sqli_dump",
        "severity": "medium",
        "base": 150,
        "hint": "UNION out of the product search (3 columns) into staff_notes",
    },
}


def generate() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA.read_text())
    n = 0
    for tid, t in TECHNIQUES.items():
        flag = f"PKTR{{{tid}_{secrets.token_hex(8)}}}"
        conn.execute(
            "INSERT OR REPLACE INTO flags "
            "(technique_id, flag, subsystem, target, effect, severity, base, location_hint) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (tid, flag, t["subsystem"], t["target"], t["effect"],
             t["severity"], t["base"], t["hint"]),
        )
        d = SECRET_DIR / t["target"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "flag.txt").write_text(flag + "\n")
        n += 1
    conn.commit()
    conn.close()
    print(f"[flags] generated {n} flag(s), wrote to {SECRET_DIR}")


if __name__ == "__main__":
    generate()
