"""Fake card authorisation for Packet River's shops and utility bills.

Card records use the standard vendor TEST PANs only (4111..., 5500..., 3400...) -
non-functional numbers, no BIN ranges, no PAN generation. Model lifted from
GIBSON/.../ztpf_engine.py `_txn_card_auth`.
"""
from __future__ import annotations

import secrets

CARDS = {
    "4111111111111111": {"name": "P. ELLIS", "exp": "03/28", "cvv": "123", "limit": 2000.0, "bal": 150.0},
    "5500000000000004": {"name": "R. SINGH", "exp": "11/27", "cvv": "456", "limit": 5000.0, "bal": 4800.0},
    "340000000000009":  {"name": "A. FINCH", "exp": "07/26", "cvv": "789", "limit": 10000.0, "bal": 300.0},
}


def _auth_code() -> str:
    return "".join(secrets.choice("0123456789") for _ in range(6))


def authorize(pan: str, exp: str, cvv: str, amount: float, force: bool = False) -> dict:
    c = CARDS.get(pan.replace(" ", ""))
    if not c:
        return {"approved": False, "rc": "14", "reason": "invalid card number"}
    if c["exp"] != exp or c["cvv"] != cvv:
        return {"approved": False, "rc": "05", "reason": "do not honour"}
    available = c["limit"] - c["bal"]
    # THE BUG: `force` skips the limit check entirely, and there is no
    # server-side sanity on `amount`.
    if amount > available and not force:
        return {"approved": False, "rc": "51", "reason": "insufficient funds / over limit"}
    c["bal"] += amount
    return {"approved": True, "rc": "00", "auth_code": _auth_code()}
