# Packet River architecture

Tracks the code as it lands. Phases 0-5 plus the recon layer are in; each phase
updates this document in the same commit series. For the per-technique detail
see [`scenarios.md`](scenarios.md) and [`districts/`](districts/); for the
end-to-end checks see [`verification.md`](verification.md).

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

The vulnerable districts: `websites` (8 storefronts + Town Hall + Police + Fire,
one PHP/Apache container), `bank` (Express: online banking, JWT `none`, account
IDOR, a grid-tied alarm panel), `db` (MariaDB), `paygw` (fake card gateway),
`field-plc` (water + power + widget-factory + sewage soft-PLCs in one container,
plus the operator HMI), `as400` (TN5250 green screen behind Town Hall),
`z16` (TN3270E green screen behind the Bank), `traffic-plc` (commanded over the
open MQTT bus), `rail-plc` (raw-TCP console + command injection), `dns` (the
town name server, AXFR wide open), and `player` (the attacker box). Cinema and
Bakery render on the map but are set dressing. Phase 5 adds two network-attack
lanes: `netlab` / `netlab-patron` (the Diner's open Wi-Fi, a sniffable LAN
standing in for 802.11) and `soho-router` / `soho-resident` (a consumer router
on the edge of town that pivots a residential foothold into the rail console).

## Services

| Service | Stack | Role |
|---|---|---|
| `gateway` | nginx:alpine | The only way in. Proxies `/`, `/api/state`, `/ws` → `simmap` and `/api/score/*` → `scoring`. Writes a JSON access log to the `gw-logs` volume for the Alert-Level tailer. (Real `Host:`-header vhost routing for the 8 shops is still a roadmap item; today the shop names all land on `websites` directly.) |
| `simmap` | python:3.12-slim, Flask + flask-sock (gunicorn `-k gevent`) + paho-mqtt | The town state model, a 1 s tick loop, a coarse physics pass, the Modbus client loops to `field-plc` (`icsloops.py`), the MQTT bridge, `logtail.py`, the Alert/blue-team threads, the WebSocket feed, and the map UI (pixel-art base image + a calibrated live SVG overlay from `web/overlay.json`). Subscribes `pkt/score/events` and breaks the named part of the town on a valid submission. |
| `scoring` | python:3.12-alpine, Flask + paho-mqtt | Owns `scoring.db` (SQLite) and the flags. `flags.py` mints a random `PKTR{...}` per technique at boot and drops each onto the shared `pkt-flags` volume; `creds.py` mints the per-plant HMI operator logins. `auth.py` = HMAC signed-cookie sessions + scrypt. `POST /api/score/{register,login,logout,run,arm,submit}`, `GET /me` + `/leaderboard`. The only write path is `submit {flag}`; points are a pure function of a valid random flag + server-held timing. On a hit it publishes `pkt/score/events`; on `pkt/creds/rotate` it re-mints the HMI creds. |
| `bus` | eclipse-mosquitto:2 | Event bus for `pkt/#`, and a target: `pkt/traffic/#` is world-writable in the flat build. Authenticated with per-topic ACLs in the segmented build. |
| `db` | mariadb:11 | Real MySQL (the SQLi syllabus needs `information_schema`, `UNION`, verbose errors). One schema per shop, seeded from `db/init/`. Capped buffer pool. |
| `websites` | php:8.2-apache | The 8 Main Street storefronts + Town Hall + Police + Fire, one lifted bug per vhost, each behind a login portal. Its entrypoint plants each site's flag. Published on `127.0.0.1:8090`. |
| `bank` | node:20-alpine, Express | First Packet Bank & Trust: login portal, customer dashboard, JSON accounts API (`alg:none` JWT, account IDOR), a mock ATM, and an alarm panel whose state follows the industrial power feeder. In-memory ledger. `127.0.0.1:8100`. |
| `paygw` | python:3.12-alpine, Flask | Fake card gateway every checkout posts to. IDOR on `GET /receipt/<txn>`. Vendor **test** PANs only. `127.0.0.1:8500`. |
| `field-plc` | python:3.12-slim + pymodbus | Four real Modbus/TCP soft-PLCs in one container - water (:502), power (:503), widget-factory (:504), sewage (:505) - plus the shared Flask operator HMI (`:8093`, per-plant rotating creds, a Cross Creek-style mimic per plant). A 0.3 s scan loop runs the golden program and, when `MODBUS_WRITE_OPEN=0`, re-asserts the safe state every pass and clamps setpoints. Each plant's flag sits in an input-register block gated by the maintenance-mode coil. |
| `as400` | web3270 mock (TN5250) | The Packet River AS/400 behind Town Hall. Blank sign-on + a shipped default + a public payroll library. `127.0.0.1:8992`. |
| `z16` | web3270 mock (TN3270E) | The Packet River IBM z16 behind the Bank. Never-revoked default admin + a WARNING-mode world-readable RACF profile. `127.0.0.1:8991`. |
| `traffic-plc` | python:3.12-alpine + paho-mqtt | Five signal controllers; takes each intersection's commanded mode off `pkt/traffic/<id>/set` (no ACL on the flat broker - the bug). An engineering-mode topic takes a short PIN and publishes the flag. Read-only status on `:8095`. |
| `rail-plc` | python:3.12-alpine | The loop/spur switch controller. Raw-TCP "maintenance console" on `:2323` with default creds and a `set label` that shells out (command injection). Publishes `pkt/rail/switch`. Read-only status on `:8096`. |
| `dns` | alpine + CoreDNS | The town name server. Authoritative for `packetriver.range` (CNAMEs onto the container network), forwards the rest to Docker's embedded resolver. **AXFR is open to anyone** - the `dns_axfr` technique. Binds only its fixed it-net address (`172.31.20.253`) so it doesn't shadow `127.0.0.11`. |
| `netlab` / `netlab-patron` | python:3.12-alpine | Phase 5a. `netlab` is the Diner's open-Wi-Fi "AP": a cleartext rewards portal (:80) + a toy POP3 (:110), plus an ARP-cache watcher that feeds Alert heat. `netlab-patron` signs in and reads mail over the segment on a loop. Both on `lan-net`; no published ports. |
| `soho-router` / `soho-resident` | python:3.12-alpine | Phase 5b. `soho-router` is a consumer router: WAN-side admin reachable, still `admin/admin`, a Diagnostics packet-capture that returns a decoded dump. `soho-resident` (a rail engineer) signs in to a cleartext crew portal on a loop. `soho-router` on `home-net` + `it-net`; `soho-resident` on `home-net` only. |
| `player` | python:3.12-slim + tools | The boxed-in attacker box: sqlmap, nmap, curl, dig, mosquitto-clients, pymodbus, tcpdump, dsniff, plus the pure-Python `as400_5250.py` / `z16_3270.py` green-screen clients and a `ttyd` terminal (`:7681`). Its resolver is `dns`. Default route dropped at start; `NET_ADMIN` + `NET_RAW` + `ip_forward=1` for the layer-2 lane; `scripts/targets.py` is a lab-only allowlist guard. |

## Networks

Five bridges. All but `edge-net` are `internal: true` (no route off-box);
`edge-net` faces the host so published ports have a route back.

- `edge-net` - `gateway` + every service that publishes a port. A container
  attached only to internal networks can't publish reliably, so the
  port-publishing services are dual-homed here and on `it-net`.
- `it-net` (`internal`) - the main lab segment: `gateway`, `simmap`, `scoring`,
  `db`, `websites`, `bank`, `paygw`, `field-plc`, `as400`, `z16`, `traffic-plc`,
  `rail-plc`, `dns`, `bus`, `soho-router`, `player`.
- `bus-net` (`internal`) - `bus`, `simmap`, `scoring`, `traffic-plc`, `rail-plc`,
  `netlab`.
- `lan-net` (`internal`, `172.31.60.0/24`) - the Diner Wi-Fi: `netlab` (.10),
  `netlab-patron` (.20), `player`. Phase 5a.
- `home-net` (`internal`, `172.31.61.0/24`) - a resident's home LAN behind the
  SOHO router: `soho-router` (.10), `soho-resident` (.20). Phase 5b. `player`
  is NOT on it - the pivot goes through the router's WAN-side admin.

There is no separate `ot-net` in the current build - the PLC protocol ports sit
on `it-net`. The Phase-4 pivot-isolation goal (move `player` off the OT segment
so it reaches the PLCs only after a foothold on `websites`) is not done yet;
`status.sh` flags it. `player`'s resolver is the `dns` container
(`172.31.20.253`), set via compose `dns:`.

## Anti-cheat

The flag string is the only currency. It exists only in `scoring.db` and inside
the one vulnerable resource it was planted in, never in simmap, the browser, or
the `player` box (which does not mount `pkt-flags`). `submit` needs a session
and an active run, one accepted flag per (run, technique), and wrong guesses
just return `{accepted:false}` (no "close" hint) while ticking Alert heat up.
Points are a pure server-side function of a valid random flag plus server-held
timing / Alert state - no client-supplied score, multiplier, or
technique-complete field is trusted. `instructor/ctf/check-flags.sh`
smoke-tests the whole mint → plant → submit → score loop.

Every published port binds to `127.0.0.1`. `lib.sh:assert_loopback_only` parses
`docker compose config` and refuses to start if any `published:` port lacks
`host_ip: 127.0.0.1`. `status.sh` re-audits the running bindings and checks the
`player` box cannot reach the internet (the pivot-isolation check is aspirational
- see Networks).

## The OT loop (`simmap/icsloops.py`)

`simmap` is a Modbus *client* to `field-plc`. One thread per plant (water,
power, widget-factory, sewage): read the coils and setpoints, step the
matching model (`WaterModel` / `PowerModel` / `factory` / `SewageModel`, coarse
first-order integrators - stop the pump and pressure bleeds out over a few
ticks), write the PVs back so the HMI stays live, and mirror the derived state
into `TownState`. Those subsystems are listed in `town.external`, so the
built-in idle physics leaves them alone. The debug-menu effects and
`pkt/reset {scope:...}` call the same `icsloops` pokes, which issue the same
Modbus writes an attacker would - so a button and an attack are identical.

Traffic and rail are held by their own containers and reach `simmap` over MQTT
(`pkt/traffic/+/state`, `pkt/rail/switch`); the crash and derail physics stay
in `models/town.py`. Setting the rail switch to `spur` before the train reaches
the branch routes it onto the spur polyline (`rail.on_spur` / `spur_pos`); it
runs the spur to the Widget Factory over ~5 s, then `derailed` + `on_fire`.

## Recon layer (`dns/`)

The `dns` container is authoritative for `packetriver.range` and is the
`player` box's resolver. The zone answers AXFR from anyone; the CNAMEs point at
`packetriver-<svc>.` and CoreDNS forwards those (and bare container names) to
Docker's embedded resolver. See [`districts/recon.md`](districts/recon.md).

## The town state model (`simmap/models/town.py`)

One `@dataclass` per subsystem, golden defaults, plain floats and bools:
`Intersection` x4, `Rail`, `Water`, `Sewage`, `Power`, `Shop` x8 (keyed:
generalstore, hardware, pharmacy, diner, barber, tavern, drycleaner,
baittackle), `Bank` (balance, `alarm_armed`, `atm_drained`), `Civic` x2
(police, fire), `CityHall`, `Alert`. `TownState.step(dt)` advances all of them
once per tick with coarse first-order-lag math (open a feeder and the frequency
sags; open the sewage bypass and the river contamination integrates up until
the swimmers get sick; the bank alarm follows the industrial feeder unless it
was cut). `snapshot()` flattens everything and adds a monotonic `state_seq`; that dict
is what every client renders onto the overlay.

### The map overlay (`simmap/web/`)

`index.html` layers a transparent `<svg>` over `basemap.png`. `app.js` fetches
`overlay.json` (percentage coords, `0..1`, for every building hotspot, traffic
signal, streetlight, the residential power / water dots, the rail path + spur,
the river, the swimmers, and the water / power flow lines), builds the overlay elements once, then mutates their `fill` /
`class` / `visibility` from each snapshot. Clicking a building hotspot opens its
service (Phase 1+); Phase 0 just names it. `overlay.json` is pinned to the
current base art and gets re-calibrated when the image changes, open the map
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
- **Traffic + rail** (Phase 4) are held by their own containers. `traffic-plc`
  takes each intersection's commanded mode off `pkt/traffic/<id>/set` (no ACL
  on the flat broker - that is the bug) and republishes `pkt/traffic/<id>/state`;
  `rail-plc` publishes `pkt/rail/switch` from its raw-TCP console. `simmap`
  subscribes to both and mirrors them onto `TownState`; the crash / derail
  physics stay in `models/town.py`.
- **Alert Level + blue team** (Phase 4): `models/town.py` runs the leaky-bucket
  heat meter (half-life ~2 min, downward hysteresis). Heat comes from event
  severity (`bus.py`), wrong submissions, and `logtail.py` reading the
  gateway's JSON access log off a shared volume for scan bursts. On each level
  rise the tick loop calls `blueteam.py`: L2 rotates the traffic PIN, the rail
  console password (`pkt/reset {scope:"creds"}`), and the field-plc HMI
  operator logins (`pkt/creds/rotate` → `scoring` re-mints; the new set shows
  on `GET /ops/handover.txt`), L5 auto-restores the worst-hit subsystem.
  `pkt/alert/level` is published for `scoring`. Already-solved techniques stay
  solved.
- **Segmented build:** `./start.sh --segmented` folds in
  `docker-compose.segmented.yml` - `MODBUS_WRITE_OPEN=0`, an authenticated
  broker (`bus/mosquitto.segmented.conf` + `acl.segmented` + `passwd.segmented`)
  with each `pkt/*` topic scoped to its owner, and every default credential
  rotated.
- Every tick, `simmap` also broadcasts the full snapshot to every `/ws` client.
  New clients get a full snapshot on connect and on `{"type":"resync"}`; the UI
  reconnects with backoff and derives all animation from state, never from
  having seen every event.

