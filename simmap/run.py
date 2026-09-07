"""simmap entrypoint: boot the town, the tick loop, the MQTT bridge, and Flask."""
from __future__ import annotations

import os
import threading
import time

import icsloops
import server
from bus import Bus
from models import TownState


def main() -> None:
    town = TownState()
    lock = threading.Lock()
    server.STATE["town"] = town
    server.STATE["lock"] = lock

    bus = Bus(town, lock, on_change=server.broadcast)
    server.BUS = bus
    threading.Thread(target=bus.start, daemon=True).start()

    # the water + power districts are driven by the real Modbus PLCs in
    # field-plc; take those subsystems off the built-in idle physics.
    town.external.update({"water", "power", "factory", "sewage"})
    icsloops.start(town, lock)

    tick = float(os.environ.get("TICK_SECONDS", "1.0"))

    def loop() -> None:
        last = time.time()
        while True:
            time.sleep(tick)
            now = time.time()
            dt = now - last
            last = now
            with lock:
                town.step(dt)
                snap = town.snapshot()
            try:
                bus.publish_state(snap)
            except Exception:
                pass
            server.broadcast()

    threading.Thread(target=loop, daemon=True).start()

    server.app.run(host="0.0.0.0", port=8000, threaded=True)


if __name__ == "__main__":
    main()
