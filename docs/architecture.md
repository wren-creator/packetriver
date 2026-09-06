# Packet Creek architecture

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

Later phases hang the vulnerable districts off `gateway` (by `Host:` header)
and off the OT network: `websites` (8 shops + City Hall, one PHP/Apache
container), `db` (MariaDB), `paygw` (fake card gateway), `field-plc` (water +
sewage + electric soft-PLCs in one container), `traffic-plc`, `rail-plc`, and
`player` (the attacker box).

## Services (Phase 0)

| Service | Stack | Role |
|---|---|---|
| `gateway` | nginx:alpine | Reverse proxy and, later, vhost router. Proxies `/` and `/api/state` and `/ws` to `simmap`, `/api/score/*` to `scoring`. Writes a JSON access log (a shared volume for the Alert-Level tailer arrives in Phase 4). |
| `simmap` | python:3.12-slim, Flask + flask-sock + paho-mqtt | The town state model, a 1 s tick loop, a coarse physics pass, the MQTT bridge, the WebSocket feed, and the inline-SVG map UI. Serves the UI itself; `gateway` just proxies. |
| `scoring` | python:3.12-alpine, Flask + paho-mqtt | Owns `scoring.db` (SQLite on a named volume). Phase 0 is schema + health + stubs; Phase 1 adds flag generation/injection, auth, submission validation, the score formula, and the leaderboard. |
| `bus` | eclipse-mosquitto:2 | Event bus for `pkt/#`, and a target: `pkt/traffic/#` is world-writable in the flat build. |

## Networks

- `edge-net` (bridge) - `gateway`, and later `player`. Faces the host.
- `it-net` (bridge, `internal: true`) - `gateway`, `simmap`, `scoring`, `bus`, and later `websites`, `db`, `paygw`.
- `bus-net` (bridge, `internal: true`) - `bus`, `simmap`, `scoring`, and later `traffic-plc`.
- `ot-net` (bridge, `internal: true`) - added in Phase 2 for the PLC protocol endpoints and their HMIs. The `player` box never joins it; OT is reachable only after a pivot through `websites`.

Every published port binds to `127.0.0.1`. `lib.sh:assert_loopback_only` parses
`docker compose config` and refuses to start if any `published:` port lacks
`host_ip: 127.0.0.1`. `status.sh` re-audits the running bindings and, once the
`player` box exists, checks it cannot reach the internet or the OT segment.

## The town state model (`simmap/models/town.py`)

One `@dataclass` per subsystem, golden defaults, plain floats and bools:
`Intersection` x4, `Rail`, `Water`, `Sewage`, `Power`, `Shop` x8, `CityHall`,
`Alert`. `TownState.step(dt)` advances all of them once per tick with coarse
first-order-lag math (open a feeder and the frequency sags; open the sewage
bypass and the river contamination integrates up until the swimmers get sick).
`snapshot()` flattens everything, adds the derived per-house water/power state
and a monotonic `state_seq`, and that dict is what every client renders.

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

## Anti-cheat (from Phase 1)

There is no "award points" endpoint. The only write path is
`POST /api/score/submit {flag}`, and points are a pure server-side function of
a valid random flag plus server-held timing and Alert state. Flags are minted
per `docker compose up`, written to a shared volume mounted read-only into only
the one target that owns each, and never reach `simmap`, the browser, or the
`player` box.
