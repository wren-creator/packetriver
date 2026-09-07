#!/usr/bin/env python3
"""Packet River loop-track switch + spur controller.

A raw-TCP "maintenance console" on :2323. The switch position it holds is
published on pkt/rail/switch; simmap reads it and moves the train. Throw the
switch to the spur just as the train reaches the branch and it derails into
the Widget Factory.

Deliberate weaknesses:
  * default credentials `maint` / `maint`
  * `set label <text>` passes the text straight to a shell (os.popen), so it
    is a command-injection foothold, not just a label field
  * `flag` prints this session's flag to any signed-on console

A read-only status page sits on :8096 as the recognisable front door.
"""
import os
import secrets
import socket
import subprocess
import threading

import paho.mqtt.client as mqtt
from flask import Flask

MQTT_HOST = os.environ.get("MQTT_HOST", "bus")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
USER = os.environ.get("CONSOLE_USER", "maint")
PASS = os.environ.get("CONSOLE_PASS", "maint")   # rotated by the blue team at Alert L2
_ORIG_PASS = PASS
# a second operator account - the rail engineer's, reused on the crew web portal
# the SOHO-router lane sniffs (Phase 5b). Static: credential reuse is the lesson.
CREW_USER = os.environ.get("RAIL_CREW_USER", "rse.kmiller")
CREW_PASS = os.environ.get("RAIL_CREW_PASS", "Sw1tchboard!")
PORT = 2323

try:
    with open("/run/secret/rail_console/flag.txt") as f:
        FLAG = f.read().strip()
except OSError:
    FLAG = "PKTR{rail_console_flag_missing}"

switch = {"position": "loop", "label": "MAIN-LOOP-SW"}
_cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="rail-plc")
if os.environ.get("MQTT_USER"):
    _cli.username_pw_set(os.environ["MQTT_USER"], os.environ.get("MQTT_PASS", ""))


def publish_switch():
    _cli.publish("pkt/rail/switch", '{"position": "%s"}' % switch["position"], retain=True)


def _on_connect(c, u, flags, rc, props):
    c.subscribe("pkt/reset")
    publish_switch()


def _on_message(c, u, msg):
    global PASS
    import json as _j
    try:
        scope = _j.loads(msg.payload.decode() or "{}").get("scope", "all")
    except ValueError:
        scope = "all"
    if scope in ("all", "rail"):
        switch["position"] = "loop"
        switch["label"] = "MAIN-LOOP-SW"
        PASS = _ORIG_PASS                      # golden restore includes the creds
        publish_switch()
        print("[rail-plc] reset -> switch loop, creds restored")
    elif scope == "creds":
        PASS = secrets.token_hex(6)            # blue-team L2 rotation
        print("[rail-plc] console password rotated")


_cli.on_connect = _on_connect
_cli.on_message = _on_message


BANNER = (
    "\r\n=== PACKET RIVER & SOUTHERN RAILROAD - DISPATCH - LOOP/SPUR SWITCH ===\r\n"
    "  model RSC-2 firmware 1.4    unit: MAIN-LOOP-SW\r\n"
    "  type 'login <user> <pass>' to sign on, 'help' for commands\r\n\r\n"
)
HELP = (
    "  login <user> <pass>   sign on to the console\r\n"
    "  status                show switch position\r\n"
    "  set switch loop|spur  move the switch\r\n"
    "  set label <text>      set the unit label\r\n"
    "  flag                  show the maintenance key\r\n"
    "  quit                  disconnect\r\n"
)


def handle(conn, addr):
    conn.sendall(BANNER.encode())
    authed = False
    f = conn.makefile("rwb", buffering=0)
    try:
        for raw in f:
            line = raw.decode(errors="replace").strip()
            if not line:
                conn.sendall(b"> ")
                continue
            parts = line.split()
            cmd = parts[0].lower()

            if cmd == "help":
                conn.sendall(HELP.encode())
            elif cmd == "login":
                ok = len(parts) >= 3 and (
                    (parts[1] == USER and parts[2] == PASS)
                    or (parts[1] == CREW_USER and parts[2] == CREW_PASS))
                if ok:
                    authed = True
                    conn.sendall(b"OK - signed on\r\n")
                else:
                    conn.sendall(b"login failed\r\n")
            elif cmd == "quit" or cmd == "exit":
                conn.sendall(b"bye\r\n")
                break
            elif not authed:
                conn.sendall(b"not signed on - use 'login <user> <pass>'\r\n")
            elif cmd == "status":
                conn.sendall(f"switch={switch['position']} label={switch['label']}\r\n".encode())
            elif cmd == "flag":
                conn.sendall((FLAG + "\r\n").encode())
            elif cmd == "set" and len(parts) >= 3 and parts[1] == "switch":
                pos = parts[2].lower()
                if pos in ("loop", "spur"):
                    switch["position"] = pos
                    publish_switch()
                    conn.sendall(f"switch -> {pos}\r\n".encode())
                else:
                    conn.sendall(b"usage: set switch loop|spur\r\n")
            elif cmd == "set" and len(parts) >= 3 and parts[1] == "label":
                text = line.split(None, 2)[2]
                switch["label"] = text[:40]
                # BUG: the label is handed straight to a shell
                out = subprocess.run(
                    f"echo {text} | logger -t railswitch; echo {text}",
                    shell=True, capture_output=True, text=True, timeout=5)
                conn.sendall(("label set\r\n" + out.stdout + out.stderr).encode())
            else:
                conn.sendall(b"?\r\n")
            conn.sendall(b"> ")
    except OSError:
        pass
    finally:
        conn.close()


def tcp_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", PORT))
    s.listen(8)
    print(f"[rail-plc] maintenance console on :{PORT} ({USER}/{PASS})")
    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


app = Flask(__name__)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/state")
def api_state():
    return dict(switch)


@app.get("/")
def index():
    return (
        "<!doctype html><meta charset=utf-8><title>Packet River &amp; Southern Railroad - Dispatch</title>"
        "<style>body{font:15px/1.5 system-ui;background:#f3ecdd;color:#3b3226;margin:0}"
        ".bar{background:#fffdf7;border-bottom:2px solid #e4d8bf;padding:12px 20px;font-weight:800}"
        "main{max-width:480px;margin:24px auto;padding:0 20px}</style>"
        "<div class=bar>PACKET RIVER &amp; SOUTHERN RAILROAD &mdash; Dispatch &middot; loop/spur switch</div>"
        f"<main><p>Unit <b>{switch['label']}</b></p>"
        f"<p>Switch position: <b>{switch['position'].upper()}</b></p>"
        "<p style=color:#8c7d64>Read-only. The switch is set from the field console (TCP 2323).</p></main>")


def _mqtt_loop():
    while True:
        try:
            _cli.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            break
        except OSError:
            threading.Event().wait(2)
    _cli.loop_start()


if __name__ == "__main__":
    threading.Thread(target=_mqtt_loop, daemon=True).start()
    threading.Thread(target=tcp_server, daemon=True).start()
    app.run(host="0.0.0.0", port=8096, threaded=True, use_reloader=False)
