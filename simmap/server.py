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
        "phase": 4,
        "eggs": os.environ.get("PKT_EGGS", "off"),
    }


_EGGS = os.environ.get("PKT_EGGS", "off")
_GOSSIP = {
    "subtle": [
        "the Diner never put a password on the wifi. everyone just hops on.",
        "that house out past the tracks, the router's still on whatever it shipped with.",
        "the traffic box downtown will take an instruction from about anyone.",
        "somebody left the whole phone book on the town's name server.",
    ],
    "obvious": [
        "the Diner's guest wifi is wide open and nothing on it is encrypted - a "
        "credential and a whole inbox go across it in the clear.",
        "the rail engineer past the tracks works from home on a router still set to "
        "admin/admin, and its diagnostics page will dump the LAN traffic for you.",
        "the traffic controllers take their orders off the message bus with no "
        "authentication - publish to the right topic and a crossroads locks green.",
        "the town DNS answers a zone transfer to anyone, and there's a stale record "
        "in it nobody cleaned up.",
    ],
}


_DIRECTORY = [
    ("Packet River Municipal Water Authority", "water.packetriver.range", "Public Works"),
    ("Packet River Water Reclamation Facility", "reclamation.packetriver.range", "Public Works"),
    ("Packet River Power & Light", "power.packetriver.range", "Public Works"),
    ("Packet River Widget Works", "widgetworks.packetriver.range", "Industry"),
    ("Packet River DOT - Signal Operations", "signals.packetriver.range", "Transportation"),
    ("Packet River & Southern Railroad - Dispatch", "dispatch.packetriver.range", "Transportation"),
    ("First Packet Bank & Trust", "firstpacketbank.packetriver.range", "Finance"),
    ("FPB&T Core Banking", "core.firstpacketbank.packetriver.range", "Finance"),
    ("Packet River Payroll Bureau", "payroll.packetriver.range", "Finance"),
    ("Packet River Merchant Services", "merchant.packetriver.range", "Finance"),
    ("Town of Packet River - Borough Hall", "townhall.packetriver.range", "Civic"),
    ("Packet River Police Department", "pd.packetriver.range", "Civic"),
    ("Packet River Fire & Rescue", "fd.packetriver.range", "Civic"),
    ("Packet River General Store", "generalstore.packetriver.range", "Main Street"),
    ("Riverside Hardware & Supply", "hardware.packetriver.range", "Main Street"),
    ("Packet River Pharmacy", "pharmacy.packetriver.range", "Main Street"),
    ("The Packet River Diner", "diner.packetriver.range", "Main Street"),
    ("Riverbend Barber & Salon", "barber.packetriver.range", "Main Street"),
    ("The Broken Packet Tavern", "tavern.packetriver.range", "Main Street"),
    ("Packet River Cleaners", "cleaners.packetriver.range", "Main Street"),
    ("Packet River Bait & Tackle", "baittackle.packetriver.range", "Main Street"),
]


@app.get("/directory")
def directory():
    """A plain corporate/municipal directory. Public-facing recon fodder: it
    hands you every official name and its hostname in one page."""
    rows = "".join(
        f"<tr><td>{name}</td><td><code>{host}</code></td><td>{dept}</td></tr>"
        for name, host, dept in _DIRECTORY
    )
    html = ("<!doctype html><meta charset=utf-8><title>Packet River - Organisation Directory</title>"
            "<style>body{font:14px/1.6 system-ui;max-width:760px;margin:32px auto;padding:0 18px;color:#243}"
            "table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:6px 8px;text-align:left}"
            "code{background:#f2f4f6;padding:1px 4px}</style>"
            "<h1>Packet River - Organisation Directory</h1>"
            "<p>Systems and services on the municipal network. For access requests contact "
            "IT at <code>it@packetriver.range</code>.</p>"
            f"<table><tr><th>Organisation</th><th>Host</th><th>Group</th></tr>{rows}</table>")
    return html, 200, {"Content-Type": "text/html"}


@app.get("/whois")
def whois():
    """A toy whois-over-HTTP. `/whois?q=<name>` returns a record for a known
    hostname or org substring."""
    q = (request.args.get("q") or "").strip().lower()
    if not q:
        return ("usage: /whois?q=<hostname or organisation>\n", 200,
                {"Content-Type": "text/plain"})
    for name, host, dept in _DIRECTORY:
        if q in host.lower() or q in name.lower():
            body = (f"organisation:  {name}\n"
                    f"host:          {host}\n"
                    f"group:         {dept}\n"
                    f"registrar:     Town of Packet River, IT\n"
                    f"contact:       it@packetriver.range\n"
                    f"nameserver:    ns.packetriver.range\n")
            return body, 200, {"Content-Type": "text/plain"}
    return (f"no match for '{q}'\n", 404, {"Content-Type": "text/plain"})


@app.get("/robots.txt")
def robots():
    if _EGGS == "off":
        return "User-agent: *\nDisallow:\n", 200, {"Content-Type": "text/plain"}
    return ("User-agent: *\nDisallow: /hints\n"
            "# the town talks. /hints\n"), 200, {"Content-Type": "text/plain"}


@app.get("/hints")
def hints():
    if _EGGS == "off":
        return "not found\n", 404, {"Content-Type": "text/plain"}
    lines = _GOSSIP.get(_EGGS, _GOSSIP["subtle"])
    body = "things people are saying around Packet River\n" \
           "-------------------------------------------\n" + \
           "\n".join(f"- {ln}" for ln in lines) + "\n"
    return body, 200, {"Content-Type": "text/plain"}


@app.post("/api/debug/effect")
def api_debug_effect():
    data = request.get_json(force=True, silent=True) or {}
    with STATE["lock"]:
        ok = apply(STATE["town"], data.get("effect", ""), data)
        STATE["town"].add_heat(10)
    broadcast()
    return {"ok": ok}


@app.post("/api/debug/event")
def api_debug_event():
    """Fire (or clear) a timed event now. {name: news_crew|inspector|parade,
    action: start|end}. For testing and instructor demos."""
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "")
    action = data.get("action", "start")
    with STATE["lock"]:
        ev = STATE["town"].events
        if name not in ("news_crew", "inspector", "parade"):
            return {"ok": False, "error": "unknown event"}, 400
        if action == "start":
            ev._next[name] = ev.clock          # fire on the next tick
        else:
            ev._ends[name] = ev.clock
    broadcast()
    return {"ok": True, "name": name, "action": action}


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
