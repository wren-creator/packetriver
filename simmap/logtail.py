"""Turn scanner noise on the gateway into Alert heat.

The gateway writes a JSON access-log line per request to a volume shared with
simmap. This tails it and, when it sees the shape of a scan - a known tool
user-agent, a burst of 4xx, or a spray of distinct paths - it bumps the Alert
meter. Loud attacks were always going to move the meter (their event carries a
`severity`); this is what makes a careless *approach* cost you too.
"""
from __future__ import annotations

import json
import os
import threading
import time

LOG_PATH = os.environ.get("GATEWAY_LOG", "/gwlogs/access.json")
TOOL_UA = ("sqlmap", "nikto", "ffuf", "gobuster", "dirb", "nmap", "masscan",
           "wpscan", "hydra", "feroxbuster")
WINDOW = 10.0


def _tail(town, lock) -> None:
    while not os.path.exists(LOG_PATH):
        time.sleep(2)
    with open(LOG_PATH) as f:
        f.seek(0, 2)
        recent: list[tuple[float, int, str]] = []   # (ts, status, path)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            now = time.time()
            status = int(rec.get("status", 0) or 0)
            path = rec.get("uri", "")
            ua = (rec.get("ua", "") or "").lower()
            recent.append((now, status, path))
            recent[:] = [r for r in recent if now - r[0] <= WINDOW]

            heat = 0.0
            if any(t in ua for t in TOOL_UA):
                heat += 1.5                       # a scan is a slow burn, not an instant L5
            fourxx = sum(1 for _, s, _ in recent if 400 <= s < 500)
            if fourxx == 9:                       # fire once as the burst crosses
                heat += 6.0
            if len({p for _, _, p in recent}) == 16:
                heat += 6.0
            if heat:
                with lock:
                    town.add_heat(heat)


def start(town, lock) -> None:
    threading.Thread(target=_tail, args=(town, lock), daemon=True).start()
