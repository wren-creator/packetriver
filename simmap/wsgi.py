"""WSGI entrypoint for gunicorn.

Wires the town, the MQTT bridge, the ICS client loops and the 1 s tick loop
(all on daemon threads), then exposes `app`. Run with a single gevent-websocket
worker:

    gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
             -w 1 -b 0.0.0.0:8000 wsgi:app
"""
from __future__ import annotations

import os
import threading
import time

import icsloops
import server
from bus import Bus
from models import TownState

_town = TownState()
_lock = threading.Lock()
server.STATE["town"] = _town
server.STATE["lock"] = _lock

_bus = Bus(_town, _lock, on_change=server.broadcast)
server.BUS = _bus
threading.Thread(target=_bus.start, daemon=True).start()

_town.external.update({"water", "power", "factory"})
icsloops.start(_town, _lock)

_TICK = float(os.environ.get("TICK_SECONDS", "1.0"))


def _loop() -> None:
    last = time.time()
    while True:
        time.sleep(_TICK)
        now = time.time()
        dt = now - last
        last = now
        with _lock:
            _town.step(dt)
            snap = _town.snapshot()
        try:
            _bus.publish_state(snap)
        except Exception:
            pass
        server.broadcast()


threading.Thread(target=_loop, daemon=True).start()

app = server.app
