"""Signed-cookie sessions + scrypt password hashing.

Ported from webterm-3270-saas/auth/{session,password}.js: a base64url(JSON) .
base64url(HMAC-SHA256) cookie, verified with a constant-time compare, plus
scrypt salt:hash for passwords. No framework session, no external deps.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

SECRET = os.environ.get("SESSION_SECRET") or "packet-river-dev-secret-change-me"
COOKIE = "pktr_session"
TTL = 7 * 24 * 3600

_SCRYPT = dict(n=16384, r=8, p=1, dklen=64)


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _b64u_dec(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _sign(enc: str) -> str:
    return _b64u(hmac.new(SECRET.encode(), enc.encode(), hashlib.sha256).digest())


def make_cookie(user_id: int, name: str) -> str:
    payload = json.dumps({"uid": user_id, "name": name, "exp": time.time() + TTL})
    enc = _b64u(payload.encode())
    value = f"{enc}.{_sign(enc)}"
    return f"{COOKIE}={value}; HttpOnly; SameSite=Lax; Path=/; Max-Age={TTL}"


def clear_cookie() -> str:
    return f"{COOKIE}=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"


def read_session(cookie_header: str | None) -> dict | None:
    if not cookie_header:
        return None
    jar = {}
    for pair in cookie_header.split(";"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            jar[k.strip()] = v.strip()
    value = jar.get(COOKIE)
    if not value or "." not in value:
        return None
    enc, sig = value.rsplit(".", 1)
    if not hmac.compare_digest(sig, _sign(enc)):
        return None
    try:
        payload = json.loads(_b64u_dec(enc))
    except Exception:
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return {"uid": payload["uid"], "name": payload["name"]}


def hash_password(plain: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.scrypt(plain.encode(), salt=salt.encode(), **_SCRYPT).hex()
    return f"{salt}:{h}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, h = stored.split(":", 1)
    except ValueError:
        return False
    cand = hashlib.scrypt(plain.encode(), salt=salt.encode(), **_SCRYPT).hex()
    return hmac.compare_digest(cand, h)
