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
        "subsystem": "shop", "target": "generalstore", "effect": "shop_sqli_dump",
        "severity": "medium", "base": 150,
        "hint": "UNION out of the product search (3 columns) into staff_notes",
    },
    "hardware_idor": {
        "subsystem": "shop", "target": "hardware", "effect": "shop_sqli_dump",
        "severity": "quiet", "base": 100,
        "hint": "receipt.php?id= has no ownership check; receipts start at 1001",
    },
    "pharmacy_authbypass": {
        "subsystem": "shop", "target": "pharmacy", "effect": "shop_sqli_dump",
        "severity": "medium", "base": 125,
        "hint": "concatenated login query; username  ' OR role='staff' LIMIT 1 -- -",
    },
    "diner_backup": {
        "subsystem": "shop", "target": "diner", "effect": "shop_sqli_dump",
        "severity": "quiet", "base": 100,
        "hint": "a database backup was left in the web root: /diner/db_backup.sql",
    },
    "barber_xss": {
        "subsystem": "shop", "target": "barber", "effect": "shop_xss_deface",
        "severity": "medium", "base": 100,
        "hint": "stored XSS in the appointment note; the manager 'bot' writes its "
                "flag back onto your booking when the script fires",
    },
    "tavern_defaultcreds": {
        "subsystem": "shop", "target": "tavern", "effect": "shop_carded",
        "severity": "medium", "base": 125,
        "hint": "the POS/jukebox admin ships as admin / admin",
    },
    "drycleaner_gitleak": {
        "subsystem": "shop", "target": "drycleaner", "effect": "shop_sqli_dump",
        "severity": "quiet", "base": 100,
        "hint": "/drycleaner/.git/ is browsable; git-dumper it and read config.php's history",
    },
    "baittackle_ssrf": {
        "subsystem": "shop", "target": "baittackle", "effect": "shop_sqli_dump",
        "severity": "medium", "base": 150,
        "hint": "fetch.php?url= is an open SSRF; reach the localhost-only "
                "/baittackle/_internal/inv.php",
    },
    "water_modbus_pump": {
        "subsystem": "utility",
        "target": "water",
        "effect": "noop",   # the physical damage was the player's Modbus write
        "severity": "loud",
        "base": 175,
        "hint": "unauth Modbus write on :502 - stop the high-lift pump; the flag "
                "is in the input-register block that fills when you set the "
                "maintenance-mode coil (8)",
    },
    "power_modbus_feeder": {
        "subsystem": "utility",
        "target": "power",
        "effect": "noop",
        "severity": "loud",
        "base": 175,
        "hint": "unauth Modbus write on :503 - open a feeder breaker; the flag "
                "is in the input-register block gated by the maintenance-mode "
                "coil (8)",
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
