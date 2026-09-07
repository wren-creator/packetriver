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
#
# `hint` is Tier-1 orientation ONLY (see docs/learning-design.md): the bug
# class, the tool family, the surface to look at, and the fix. No working
# payloads, no exact parameters, no credentials, no path to the flag. It is
# written to scoring.db as `location_hint`. The step-by-step version - the
# "answer key" tier - lives in instructor/answer-key.md, not here and not in
# anything the player's client can pull for free.
TECHNIQUES = {
    "generalstore_sqli": {
        "subsystem": "shop", "target": "generalstore", "effect": "shop_sqli_dump",
        "severity": "medium", "base": 150,
        "hint": "Error-based SQL injection in the storefront's product search, "
                "with verbose DB errors to guide you. sqlmap, or a hand-built "
                "UNION. Fix: parameterised queries.",
    },
    "hardware_idor": {
        "subsystem": "shop", "target": "hardware", "effect": "shop_sqli_dump",
        "severity": "quiet", "base": 100,
        "hint": "IDOR on an order/receipt lookup - the record id is trusted, "
                "never checked against your session. Walk it with curl/ffuf. "
                "Fix: enforce ownership server-side.",
    },
    "pharmacy_authbypass": {
        "subsystem": "shop", "target": "pharmacy", "effect": "shop_sqli_dump",
        "severity": "medium", "base": 125,
        "hint": "Authentication bypass in the portal login - the query is "
                "string-built, so input becomes logic. Fix: prepared "
                "statements and a real auth check.",
    },
    "diner_backup": {
        "subsystem": "shop", "target": "diner", "effect": "shop_sqli_dump",
        "severity": "quiet", "base": 100,
        "hint": "A database backup got left somewhere under the web root. "
                "Content discovery - ffuf, or just read what the pages give "
                "away. Fix: keep backups out of the docroot.",
    },
    "barber_xss": {
        "subsystem": "shop", "target": "barber", "effect": "shop_xss_deface",
        "severity": "medium", "base": 100,
        "hint": "Stored XSS in the booking form; an automated 'manager' review "
                "opens each new booking, so your script runs in their context. "
                "Fix: output-encode, add a CSP.",
    },
    "tavern_defaultcreds": {
        "subsystem": "shop", "target": "tavern", "effect": "shop_carded",
        "severity": "medium", "base": 125,
        "hint": "Default credentials on the POS/jukebox admin. Try the vendor "
                "defaults, or hydra a short list. Fix: force a credential "
                "change on first use.",
    },
    "drycleaner_gitleak": {
        "subsystem": "shop", "target": "drycleaner", "effect": "shop_sqli_dump",
        "severity": "quiet", "base": 100,
        "hint": "A version-control directory is exposed under the web root - "
                "reconstruct it and read deleted history. git-dumper. Fix: "
                "don't deploy the repo; block dotfiles at the server.",
    },
    "baittackle_ssrf": {
        "subsystem": "shop", "target": "baittackle", "effect": "shop_sqli_dump",
        "severity": "medium", "base": 150,
        "hint": "SSRF in a 'fetch product image by URL' feature - point it at "
                "something only the server can reach. curl. Fix: allowlist "
                "egress, block loopback and link-local.",
    },

    # --- civic (Town Hall, Police, Fire) + payments ---
    "townhall_deface": {
        "subsystem": "civic", "target": "cityhall", "effect": "cityhall_deface",
        "severity": "loud", "base": 100,
        "hint": "A weak admin login on the announcements page, and the notice "
                "is rendered without encoding (stored XSS / defacement). Fix: "
                "real auth plus output encoding.",
    },
    "townhall_lfi": {
        "subsystem": "civic", "target": "cityhall", "effect": "cityhall_payroll",
        "severity": "loud", "base": 175,
        "hint": "Path traversal in a document viewer, reached after a weak "
                "payroll login. curl. Fix: canonicalise the path and confine "
                "it to a base directory.",
    },
    "police_leak": {
        "subsystem": "civic", "target": "police", "effect": "police_deface",
        "severity": "quiet", "base": 75,
        "hint": "A config file under the web root is world-readable. Content "
                "discovery. Fix: keep secrets out of the docroot.",
    },
    "fire_defaultcreds": {
        "subsystem": "civic", "target": "fire", "effect": "fire_deface",
        "severity": "medium", "base": 75,
        "hint": "Default credentials on the station alarm panel. Fix: change "
                "the defaults at install and don't ship shared ones.",
    },
    "as400_empmast": {
        "subsystem": "civic", "target": "cityhall", "effect": "cityhall_payroll",
        "severity": "loud", "base": 200,
        "hint": "TN5250 green screen. A weak sign-on gets you a session, and "
                "the payroll library is left readable to the public, so "
                "Interactive SQL walks right in. Fix: require passwords, "
                "rotate shipped defaults, lock down library authority.",
    },
    "paygw_receipt_idor": {
        "subsystem": "shop", "target": "paygw", "effect": "paygw_carded",
        "severity": "loud", "base": 150,
        "hint": "IDOR on the card gateway's receipt endpoint - no auth, "
                "sequential ids. curl. Fix: authorise every read.",
    },

    # --- First Packet Bank & Trust ---
    "bank_jwt_none": {
        "subsystem": "bank", "target": "bank", "effect": "bank_drain",
        "severity": "loud", "base": 200,
        "hint": "The JWT check accepts an unsigned token (alg:none) - forge an "
                "elevated claim, and a staff-only view leaks the settlement "
                "token. Fix: pin the algorithm and verify the signature.",
    },
    "bank_account_idor": {
        "subsystem": "bank", "target": "bank", "effect": "bank_leak",
        "severity": "medium", "base": 125,
        "hint": "IDOR on the accounts API - no ownership check. Walk the "
                "account ids; one memo carries the token. Fix: enforce "
                "ownership on every account read.",
    },
    "z16_racf": {
        "subsystem": "bank", "target": "bank", "effect": "bank_drain",
        "severity": "loud", "base": 275,
        "hint": "TN3270 green screen. A never-revoked default admin still logs "
                "on; a RACF resource profile is world-readable and in WARNING "
                "mode (fail-open), with a secret parked in its metadata. The "
                "RLIST command family. Fix: revoke defaults, UACC(NONE) plus "
                "an access list, take profiles out of WARNING.",
    },
    "water_modbus_pump": {
        "subsystem": "utility",
        "target": "water",
        "effect": "noop",   # the physical damage was the player's Modbus write
        "severity": "loud",
        "base": 175,
        "hint": "Unauthenticated, unvalidated Modbus writes on the field bus - "
                "the protocol has no auth. pymodbus / modbus_attack.py. The "
                "flag block unlocks while the PLC is in maintenance mode. Fix: "
                "segment OT, source-allowlist, authenticated protocol.",
    },
    "power_modbus_feeder": {
        "subsystem": "utility",
        "target": "power",
        "effect": "noop",
        "severity": "loud",
        "base": 175,
        "hint": "Unauthenticated, unvalidated Modbus writes on the substation "
                "bus - no auth on the protocol. pymodbus / modbus_attack.py. "
                "The flag block unlocks while the PLC is in maintenance mode. "
                "Fix: segment OT, source-allowlist, authenticated protocol.",
    },
    "factory_modbus": {
        "subsystem": "utility",
        "target": "factory",
        "effect": "noop",
        "severity": "loud",
        "base": 175,
        "hint": "Unauthenticated Modbus writes to the assembly-line PLC - the "
                "safety interlocks are just coils, and nothing checks the "
                "writer. pymodbus / modbus_attack.py. The flag block unlocks "
                "in maintenance mode. Fix: segment OT, source-allowlist, "
                "authenticated protocol.",
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
        # one dir per technique (a target can own more than one)
        d = SECRET_DIR / tid
        d.mkdir(parents=True, exist_ok=True)
        (d / "flag.txt").write_text(flag + "\n")
        n += 1
    conn.commit()
    conn.close()
    print(f"[flags] generated {n} flag(s), wrote to {SECRET_DIR}")


if __name__ == "__main__":
    generate()
