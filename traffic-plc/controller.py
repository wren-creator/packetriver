#!/usr/bin/env python3
"""Packet River traffic signal controllers.

Five intersection controllers that take their commanded mode off the MQTT bus.
The physics (the green/red auto cycle, the crash counter) live in simmap; this
process just holds each intersection's mode and republishes it.

The deliberate weakness: `pkt/traffic/<id>/set` has no ACL and no auth on the
flat broker, so anyone who can reach the bus can force a signal to ALL-GREEN.
`pkt/traffic/eng` is an "engineering mode" unlock - send it the PIN (default
0000) and the controller publishes this session's flag on `pkt/traffic/flag`.

  mosquitto_pub -h bus -t pkt/traffic/1/set -m ALL-GREEN
  mosquitto_pub -h bus -t pkt/traffic/eng  -m 0000
  mosquitto_sub -h bus -t pkt/traffic/flag -C 1

A read-only status page sits on :8095 as the recognisable front door.
"""
import json
import os
import threading

import paho.mqtt.client as mqtt
from flask import Flask

MQTT_HOST = os.environ.get("MQTT_HOST", "bus")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
ENG_PIN = os.environ.get("ENG_PIN", "0000")
IDS = [1, 2, 3, 4, 5]
VALID_MODES = {"AUTO", "ALL-GREEN"}

try:
    with open("/run/secret/traffic_mqtt/flag.txt") as f:
        FLAG = f.read().strip()
except OSError:
    FLAG = "PKTR{traffic_mqtt_flag_missing}"

state = {i: {"mode": "AUTO", "phase": "auto"} for i in IDS}
_cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="traffic-plc")


def publish_state(i):
    _cli.publish(f"pkt/traffic/{i}/state", json.dumps(state[i]), retain=True)


def on_connect(c, u, flags, rc, props):
    c.subscribe("pkt/traffic/+/set")
    c.subscribe("pkt/traffic/eng")
    c.subscribe("pkt/reset")
    for i in IDS:
        publish_state(i)
    print("[traffic-plc] connected; listening on pkt/traffic/+/set (no ACL)")


def on_message(c, u, msg):
    body = msg.payload.decode(errors="replace").strip().upper()
    if msg.topic == "pkt/reset":
        try:
            scope = json.loads(msg.payload.decode() or "{}").get("scope", "all")
        except ValueError:
            scope = "all"
        if scope in ("all", "traffic"):
            for i in IDS:
                state[i]["mode"] = "AUTO"
                publish_state(i)
            c.publish("pkt/traffic/flag", "", retain=True)   # clear the retained flag
            print("[traffic-plc] reset -> all AUTO")
        return
    if msg.topic == "pkt/traffic/eng":
        if body == ENG_PIN:
            c.publish("pkt/traffic/flag", FLAG, retain=True)
            print("[traffic-plc] engineering mode unlocked -> flag published")
        else:
            print(f"[traffic-plc] eng unlock rejected: {body!r}")
        return
    # pkt/traffic/<id>/set
    parts = msg.topic.split("/")
    try:
        i = int(parts[2])
    except (IndexError, ValueError):
        return
    if i not in IDS:
        return
    mode = "ALL-GREEN" if body in ("ALL-GREEN", "ALLGREEN", "GREEN") else \
           "AUTO" if body in ("AUTO", "NORMAL", "RESET") else None
    if mode is None:
        return
    state[i]["mode"] = mode
    publish_state(i)
    print(f"[traffic-plc] intersection {i} -> {mode}")


_cli.on_connect = on_connect
_cli.on_message = on_message

app = Flask(__name__)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/api/state")
def api_state():
    return {"intersections": state, "eng_pin_len": len(ENG_PIN)}


@app.get("/")
def index():
    rows = "".join(
        f"<tr><td>Intersection {i}</td><td>{s['mode']}</td></tr>"
        for i, s in state.items())
    return (
        "<!doctype html><meta charset=utf-8><title>Packet River Traffic Control</title>"
        "<style>body{font:15px/1.5 system-ui;background:#f3ecdd;color:#3b3226;margin:0}"
        ".bar{background:#fffdf7;border-bottom:2px solid #e4d8bf;padding:12px 20px;font-weight:800}"
        "main{max-width:520px;margin:24px auto;padding:0 20px}"
        "table{width:100%;border-collapse:collapse}td{padding:6px 10px;border-bottom:1px solid #efe6d0}</style>"
        "<div class=bar>PACKET RIVER TRAFFIC CONTROL &mdash; signal status</div>"
        f"<main><table>{rows}</table>"
        "<p style=color:#8c7d64>Read-only. Signal timing is set from the field bus.</p></main>")


def _mqtt_loop():
    while True:
        try:
            _cli.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
            break
        except OSError:
            threading.Event().wait(2)
    _cli.loop_forever()


if __name__ == "__main__":
    threading.Thread(target=_mqtt_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=8095, threaded=True, use_reloader=False)
