"""MQTT plumbing for simmap.

Subscribes:
  pkt/score/events   - a valid flag was submitted (scoring). {technique_id, effect, target, severity, ...}
  pkt/reset          - restore a subsystem to golden. {scope}
  pkt/campaign       - a campaign code was entered. {chapter, techniques}

Publishes:
  pkt/sim/state              - retained full snapshot, once per tick
  pkt/sim/physical/<name>    - threshold crossings (mains_dry, river_contaminated, ...)
"""
from __future__ import annotations

import json
import os
import threading

import paho.mqtt.client as mqtt

MQTT_HOST = os.environ.get("MQTT_HOST", "bus")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))

# Heat added to the Alert meter per event severity (Phase 4 gives this its own
# module; Phase 0 keeps a stub so the meter moves).
SEVERITY_HEAT = {"quiet": 2, "medium": 10, "loud": 25, "reject": 2}


class Bus:
    def __init__(self, town, lock, on_change=None):
        self.town = town
        self.lock = lock
        self.on_change = on_change or (lambda: None)
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                   client_id="simmap")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def start(self):
        while True:
            try:
                self._client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
                break
            except OSError:
                threading.Event().wait(2)
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        for topic in ("pkt/score/events", "pkt/reset", "pkt/campaign"):
            client.subscribe(topic)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode() or "{}")
        except ValueError:
            payload = {}
        with self.lock:
            if msg.topic == "pkt/score/events":
                effect = payload.get("effect")
                if effect:
                    from effects import apply
                    apply(self.town, effect, payload)
                self.town.add_heat(SEVERITY_HEAT.get(payload.get("severity", "medium"), 10))
            elif msg.topic == "pkt/reset":
                scope = payload.get("scope", "all")
                self.town.reset(scope)
                try:
                    import icsloops
                    if scope in ("all", "water"):
                        icsloops.restore_water()
                    if scope in ("all", "power"):
                        icsloops.restore_power()
                    if scope in ("all", "factory"):
                        icsloops.restore_factory()
                except Exception as exc:
                    print("[bus] reset poke:", exc)
            elif msg.topic == "pkt/campaign":
                pass  # Phase 4
        self.on_change()

    def publish_state(self, snapshot: dict):
        self._client.publish("pkt/sim/state", json.dumps(snapshot), retain=True)

    def publish_physical(self, name: str, payload: dict | None = None):
        self._client.publish(f"pkt/sim/physical/{name}", json.dumps(payload or {}))
