"""Flask app: serves the map UI, the /api surface, and the /ws town feed.

run.py wires STATE["town"] / STATE["lock"] and starts the tick + bus threads.
All websocket sends funnel through SEND_LOCK; the tick loop is the main sender,
connection handlers only receive.
"""
from __future__ import annotations

import json
import os
import pathlib
import threading

from flask import Flask, request, send_from_directory
from flask_sock import Sock

from effects import apply
from models.town import RESET_SCOPES

WEB = pathlib.Path(__file__).parent / "web"

app = Flask(__name__)
# No ping_interval: flask-sock's simple-websocket keepalive runs a second
# thread that writes PING frames straight to the socket, bypassing SEND_LOCK
# and interleaving with the tick loop's broadcast frames ("invalid attempt to
# fragment control frame" -> the client drops and reconnects every ~25 s). The
# 1 s broadcast keeps the pipe warm and nginx's /ws proxy_read_timeout is 1h,
# so no keepalive frame is needed.
sock = Sock(app)

STATE: dict = {"town": None, "lock": None}
BUS = None

CLIENTS: set = set()
CLIENTS_LOCK = threading.Lock()
SEND_LOCK = threading.Lock()


def _snapshot() -> dict:
    with STATE["lock"]:
        return STATE["town"].snapshot()


def broadcast() -> None:
    obj = json.dumps({"type": "snapshot", **_snapshot()})
    with CLIENTS_LOCK:
        clients = list(CLIENTS)
    dead = []
    for ws in clients:
        with SEND_LOCK:
            try:
                ws.send(obj)
            except Exception:
                dead.append(ws)
    if dead:
        with CLIENTS_LOCK:
            for ws in dead:
                CLIENTS.discard(ws)


def _send(ws, obj) -> None:
    with SEND_LOCK:
        try:
            ws.send(json.dumps(obj))
        except Exception:
            pass


# -- HTTP --------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/api/state")
def api_state():
    return _snapshot()


@app.get("/api/config")
def api_config():
    return {
        "cashapp": os.environ.get("DONATION_CASHAPP", "britleywren"),
        "reset_scopes": RESET_SCOPES,
        "phase": 3,
    }


@app.post("/api/debug/effect")
def api_debug_effect():
    data = request.get_json(force=True, silent=True) or {}
    with STATE["lock"]:
        ok = apply(STATE["town"], data.get("effect", ""), data)
        STATE["town"].add_heat(10)
    broadcast()
    return {"ok": ok}


@app.post("/api/debug/reset")
def api_debug_reset():
    data = request.get_json(force=True, silent=True) or {}
    scope = data.get("scope", "all")
    with STATE["lock"]:
        STATE["town"].reset(scope)
    try:
        import icsloops
        if scope in ("all", "water"):
            icsloops.restore_water()
        if scope in ("all", "power"):
            icsloops.restore_power()
        if scope in ("all", "factory"):
            icsloops.restore_factory()
        if scope in ("all", "sewage"):
            icsloops.restore_sewage()
    except Exception as exc:
        print("[server] reset poke:", exc)
    broadcast()
    return {"ok": True, "scope": scope}


@app.get("/<path:path>")
def static_asset(path):
    return send_from_directory(WEB, path)


# -- WebSocket ---------------------------------------------------------
@sock.route("/ws")
def ws_route(ws):
    with CLIENTS_LOCK:
        CLIENTS.add(ws)
    try:
        _send(ws, {"type": "snapshot", **_snapshot()})
        while True:
            raw = ws.receive()
            if raw is None:
                break
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if msg.get("type") == "resync":
                _send(ws, {"type": "snapshot", **_snapshot()})
    finally:
        with CLIENTS_LOCK:
            CLIENTS.discard(ws)
