# Packet River architecture

First cut, tracking the code as it lands. Phase 0 is the scaffold below; each
phase adds services and updates this document in the same commit series.

## The shape of it

One `docker-compose.yml` stands up a town. A player opens the map in a browser,
signs in, and attacks the real services behind it with open-source tools. A
valid flag submission scores points and tells the simulation to break that part
of the town on screen. The bus is Mosquitto, doing double duty as the game's
event fabric and as a deliberately-open target for the traffic lights.

```
                         browser (map UI + HUD + reset panel)
                                     |  http + ws
                              +------+------+
                              |   gateway   |  nginx, vhost routing, the only way in
                              +--+-------+--+
                     /ws, /api/state |       | /api/score/*
                                +----+--+  +-+------+
                                | simmap |  | scoring |   flags live only here
                                +---+----+  +----+----+
                                    |  pub/sub    |  pub  (pkt/score/events)
                                +---+-------------+---+
                                |        bus          |  mosquitto  (also: pkt/traffic/#, open)
                                +---------------------+
```

Every target's front door is a **login portal**, styled like the Cross Creek
HMI logons and the Widgetorium `login.php`. Getting past it is the first move
of most scenarios.

Later phases hang the vulnerable districts off `gateway` (by `Host:` header)
and off the OT network: `websites` (8 storefronts + Town Hall + Police + Fire,
one PHP/Apache container), `bank` (Express: online banking, JWT `none`, account
IDOR, a grid-tied alarm panel), `db` (MariaDB), `paygw` (fake card gateway),
`field-plc` (water + power + widget-factory soft-PLCs in one container; sewage
lands in Phase 4), `as400` (TN5250 green screen behind Town Hall, Phase 3c),
`z16` (TN3270E green screen behind the Bank, Phase 3d), `traffic-plc`,
`rail-plc`, `netlab` (the Diner open-Wi-Fi sniff/MITM lane), and `player` (the
attacker box). Cinema and Bakery render on the map but are set dressing.

## Services (through Phase 2)

| Service | Stack | Role |
|---|---|---|
| `gateway` | nginx:alpine | Reverse proxy and, later, vhost router. Proxies `/` and `/api/state` and `/ws` to `simmap`, `/api/score/*` to `scoring`. Writes a JSON access log (a shared volume for the Alert-Level tailer arrives in Phase 4). |
| `simmap` | python:3.12-slim, Flask + flask-sock + paho-mqtt | The town state model, a 1 s tick loop, a coarse physics pass, the MQTT bridge, the WebSocket feed, and the map UI (a pixel-art isometric base image + a calibrated live SVG overlay from `web/overlay.json`, light palette). Subscribes `pkt/score/events` and breaks the named part of the town on a valid submission. Serves the UI itself; `gateway` just proxies. |
| `scoring` | python:3.12-alpine, Flask + paho-mqtt | Owns `scoring.db` (SQLite on a named volume) and the flags. `flags.py` mints a random `PKTR{...}` per technique at boot, records the authoritative technique -> (flag, effect, points) map, and drops each flag onto the shared `pkt-flags` volume. `auth.py` = HMAC signed-cookie sessions + scrypt. `POST /api/score/{register,login,logout,run,arm,submit}`, `GET /me` + `/leaderboard`. The only write path is `submit {flag}`; points are a pure function of a valid random flag + server-held timing. On a hit it publishes `pkt/score/events`. |
| `bus` | eclipse-mosquitto:2 | Event bus for `pkt/#`, and a target: `pkt/traffic/#` is world-writable in the flat build. |
| `db` | mariadb:11 | Real MySQL (the SQLi syllabus needs `information_schema`, `UNION`, verbose errors). Phase 1: the `generalstore` schema + seed. Capped buffer pool. |
| `websites` | php:8.2-apache | The vulnerable Main Street storefronts. Phase 1: the General Store behind its login portal, with a real concatenated-`LIKE` SQL injection in the authenticated search. Its entrypoint waits for the db and plants this session's flag into a table with no page of its own. Published on `127.0.0.1:8090` for the map UI to iframe. |
| `field-plc` | python:3.12-slim + pymodbus | Two real Modbus/TCP soft-PLCs in one container - water (:502) and power (:503) - plus a shared Flask operator HMI (:8093, default creds, read-only status). A 0.3 s scan loop runs the golden control program and, when `MODBUS_WRITE_OPEN=0`, re-asserts the safe state every pass. Each plant's flag sits in an input-register block gated by the maintenance-mode coil. |
| `player` | python:3.12-slim + tools | The boxed-in attacker box: sqlmap, nmap, curl, jq, pymodbus. Default route dropped at start; `scripts/targets.py` is a lab-only allowlist guard. `recon.py` sweeps the lab; `modbus_attack.py` drives the unauth writes against `field-plc`. |

## Networks

- `edge-net` (bridge) - `gateway`, `bus`, `websites`. Faces the host, so published ports have a route back. (`bus` and `websites` are also on `it-net`; a container only on internal networks can't publish reliably.)
- `it-net` (bridge, `internal: true`) - `gateway`, `simmap`, `scoring`, `bus`, `websites`, `db`, `player`, and later `paygw` / `bank`.
- `bus-net` (bridge, `internal: true`) - `bus`, `simmap`, `scoring`, and later `traffic-plc`.
- `ot-net` (bridge, `internal: true`) - added in Phase 2 for the PLC protocol endpoints and their HMIs. `player` moves off `it-net` in the Phase 4 hardening and reaches OT only after a pivot through `websites`.

## Anti-cheat (from Phase 1)

The flag string is the only currency. It exists only in `scoring.db` and inside
the one vulnerable resource it was planted in, never in simmap, the browser, or
the `player` box (which does not mount `pkt-flags`). `submit` needs a session
and an active run, one accepted flag per (run, technique), wrong guesses just
return `{accepted:false}`. Phase 3 tightens the `pkt-flags` mount into
`websites` to a per-target subpath so one storefront can't read another's flag.

Every published port binds to `127.0.0.1`. `lib.sh:assert_loopback_only` parses
`docker compose config` and refuses to start if any `published:` port lacks
`host_ip: 127.0.0.1`. `status.sh` re-audits the running bindings and, once the
`player` box exists, checks it cannot reach the internet or the OT segment.

## The water + power loop (`simmap/icsloops.py`)

From Phase 2, `simmap` is a Modbus *client* to `field-plc`. Two threads, one
per plant: read the coils and setpoints, step `WaterModel` / `PowerModel` (a
coarse first-order integrator - stop the pump and pressure bleeds out over a
few ticks), write the PVs back so the HMI stays live, and mirror the derived
state into `TownState`. Those subsystems are listed in `town.external`, so the
built-in idle physics leaves them alone. The debug-menu effects and
`pkt/reset {scope:water|power}` call the same `icsloops` pokes, which issue the
same Modbus writes an attacker would - so a button and an attack are identical.

## The town state model (`simmap/models/town.py`)

One `@dataclass` per subsystem, golden defaults, plain floats and bools:
`Intersection` x4, `Rail`, `Water`, `Sewage`, `Power`, `Shop` x8 (keyed:
generalstore, hardware, pharmacy, diner, barber, tavern, drycleaner,
baittackle), `Bank` (balance, `alarm_armed`, `atm_drained`), `Civic` x2
(police, fire), `CityHall`, `Alert`. `TownState.step(dt)` advances all of them
once per tick with coarse first-order-lag math (open a feeder and the frequency
sags; open the sewage bypass and the river contamination integrates up until
the swimmers get sick; the bank alarm follows the industrial feeder unless it
was cut). `snapshot()` flattens everything, adds the derived per-house
water/power state and a monotonic `state_seq`, and that dict is what every
client renders onto the overlay.

### The map overlay (`simmap/web/`)

`index.html` layers a transparent `<svg>` over `basemap.png`. `app.js` fetches
`overlay.json` (percentage coords, `0..1`, for every building hotspot, traffic
head, house, streetlight, the rail path, the river, the swimmers, the two
utility flows), builds the overlay elements once, then mutates their `fill` /
`class` / `visibility` from each snapshot. Clicking a building hotspot opens its
service (Phase 1+); Phase 0 just names it. `overlay.json` is pinned to the
current base art and gets re-calibrated when the image changes — open the map
with `?edit=1` for the drag-and-copy overlay editor (`docs/overlay-editing.md`;
`edit.js`, inert without the flag).

### Event flow

- `simmap` subscribes `pkt/score/events`. A message names an `effect` key;
  `effects.py` (a `{id: fn(town, payload)}` dispatch table) sets the initial
  condition, and the physics produces the visible consequence over the next few
  seconds. Phase 0 drives this from the UI debug menu and from test messages.
- `simmap` subscribes `pkt/reset`; `{scope}` restores one subsystem, or `all`,
  to golden.
- `simmap` publishes `pkt/sim/state` (retained, once per tick) and
  `pkt/sim/physical/<name>` on threshold crossings (Phase 4 uses these for the
  Alert meter and the cascade score bonus).
- Every tick, `simmap` also broadcasts the full snapshot to every `/ws` client.
  New clients get a full snapshot on connect and on `{"type":"resync"}`; the UI
  reconnects with backoff and derives all animation from state, never from
  having seen every event.

