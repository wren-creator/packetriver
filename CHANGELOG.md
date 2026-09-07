# Changelog

All notable changes to Packet River. Newest first.

## [Unreleased]

### Phase 3c - the Packet River AS/400 (payroll green screen)
- `mainframe/as400/`: a real TN5250 host (SIGNON panel, menu tree, DSPMSG,
  WRKUSRPRF, Interactive SQL), vendored from web3270's mock-lpar (GPL-3.0,
  attribution header) with node builtins + the local `rpg/` interpreter, no npm
  deps. One addition: a `PAYROLL/PAYKEY` file carrying this session's flag,
  dropped into the `PAYROLL` library the box already ships `*PUBLIC *ALL`.
- `as400` compose service on `127.0.0.1:8992` (container port 3272), `it-net` +
  `edge-net`, reads the flag from `/run/secret/as400_empmast/flag.txt`.
- `scoring/flags.py`: `as400_empmast` technique (subsystem `civic`, effect
  `cityhall_payroll`, base 200, `loud`). Submitting it drains Town Hall's
  payroll on the map - the same effect the Town Hall web LFI chains into.
- `player`: `scripts/as400_5250.py`, a purpose-built TN5250 client (like
  `modbus_attack.py`) - negotiates the 5250 telnet options, signs on with a
  blank / default password, runs `STRSQL: SELECT * FROM PAYROLL.PAYKEY`, scrapes
  the flag. `pktr-connect` (the `ttyd` menu) gets it as option 1, plus a
  free-form `SELECT * FROM lib.table` prompt as option 2. `targets.py` allowlist
  gains `as400`. (No arm64 `tn5250` package exists, hence the built client.)
- `overlay.json`: Town Hall already carried `terminal: 7681` - clicking it on
  the map now opens the AS/400 terminal alongside the web front door.
- `docs/districts/mainframe.md`: surfaces, the three stacked IBM i
  misconfigurations (blank sign-on, default `QSECOFR`, `*PUBLIC *ALL`), the
  wire-format notes for the client, the hardening, real-world parallels.
- Verified end to end from the player box: sign on -> `STRSQL` -> flag ->
  submit -> `accepted`, 450 pts (200 x 1.5 speed x 1.5 stealth), Town Hall
  payroll reads 0 on the map, alert level ticks to 1.

### Phase 3b - Widget Factory PLC (assembly line + train loading)
- `field-plc` gains a third Modbus/TCP soft-PLC on container port 504
  (`127.0.0.1:5504`): assembly-line conveyor with an e-stop interlock, plus the
  train-loading gantry / hopper gate / car-in-position sensor. `maps.py`
  `FACTORY` block, `store.py` `FCTX/FLOCK`, `run.py` third `_serve` thread +
  scan-loop hardening + flag block.
- `simmap/models/factory.py` (`FactoryModel`) + a factory loop in `icsloops.py`:
  simmap reads the coils/DIs each tick and drives `Factory.throughput_pct`,
  `line_running`, `line_jam`, `estop_bypassed`. Throughput collapses on a jam or
  a stopped line; overspeed past the interlock caps it and runs unsafe.
- `scoring/flags.py`: `factory_modbus` (base 200, `loud`). `modbus_attack.py`
  gains a `factory` plant (`line-stop`, `estop-bypass`, `hopper-dump`, `flag`,
  `restore`). `overlay.json`: the factory hotspot opens the shared HMI; the
  render shows a line-jam ring and, on a spur derail, a fire ring.
- Reset panel gains a `factory` scope; `pkt/reset` + `/api/debug/reset` call
  `icsloops.restore_factory`.

### Phase 3a-3 - First Packet Bank & Trust
- `bank`: `node:20-alpine` Express online-banking service on `127.0.0.1:8100`.
  Hand-rolled JWT whose `verify()` honours `alg: none` (accepts an unsigned
  payload); `GET /api/accounts/:id` has no ownership check; `POST /api/transfer`
  sweeps every account. `GET /dashboard` (staff view) prints the wire token;
  account 1003's memo carries the IDOR flag.
- `scoring/flags.py`: `bank_jwt_none` (base 250, `loud`) and `bank_account_idor`
  (base 150, `quiet`), both read from per-technique `/run/secret` subpaths.
- `overlay.json`: the Bank hotspot opens online banking. The map's bank alarm
  follows the business feeder; draining the bank cuts it.

### Phase 3a-2 - Town Hall, Police, Fire, and the payment gateway
- Town Hall (`/townhall/`): announcements rendered raw (stored XSS / deface),
  a clerk/clerk admin, a concatenated-query payroll login, and `payslip.php`
  with an unsanitised `readfile()` (LFI). Techniques `townhall_deface` (base
  150) and `townhall_lfi` (base 175). `flags.py` now writes one dir per
  technique so a single target can own several.
- Police (`/police/`): a static blotter plus `dispatch/config.json` with a
  `radio_key` (`police_leak`, base 100). Fire (`/fire/`): `admin`/`fire` on the
  station alarm panel (`fire_defaultcreds`, base 75).
- `paygw`: `python:3.12-alpine` fake card gateway on `127.0.0.1:8500`. GIBSON-
  style `authorize()` with standard vendor **test** PANs only; `POST /charge`
  has a `force` bypass and no amount sanity check; `GET /receipt/<txn_id>` is an
  in-memory IDOR, one memo holding the flag (`paygw_receipt_idor`, base 150).
  Shop checkouts post here.
- `db/init/30-civic.sql`: the `townhall` schema (announce, clerk admin, payroll
  users). `overlay.json`: Town Hall / Police / Fire hotspots wired to their
  subpaths.

### Phase 3a-1 - the rest of Main Street (8 storefronts)
- `websites` restructured: one docroot, one subdirectory per shop
  (`/generalstore/`, `/hardware/`, ...), each its own MariaDB schema. Shared
  kit in `site/lib/` (schema picked from the running script's directory,
  relative-link portal, generic storefront). A Main Street directory at `/`.
- Seven new storefronts, each a distinct verified bug: hardware (IDOR on
  `receipt.php`), pharmacy (auth-bypass in the portal login), diner (a
  `db_backup.sql` in the web root), barber (stored XSS + a regex "manager bot"
  that writes its flag onto your booking), tavern (default creds `admin`/`admin`
  on the POS admin), drycleaner (browsable `.git`, `git-dumper` + `git log -p`),
  baittackle (SSRF in `fetch.php?url=` to a localhost-only inventory endpoint).
- `db/init/` is now a directory mount; `20-mainstreet.sql` builds the seven
  schemas + grants + seed. The `websites` entrypoint plants the DB-row flags
  (hardware, pharmacy), writes the diner backup, builds the drycleaner `.git`
  history, and runs the barber bot loop.
- `scoring/flags.py`: seven new techniques. `player` image gains `git` +
  `git-dumper`. `overlay.json`: every shop hotspot wired with its port +
  subpath, so clicking it on the map opens that storefront.
- Verified: every shop's exploit extracts and submits its flag; the shop shows
  `db_dumped` / `defaced` / `carded` on the map; chain bonus stacks across the
  run.

### Phase 2 - the water and power districts, on real Modbus
- `field-plc`: one container, two real Modbus/TCP soft-PLCs - water treatment +
  distribution (:502) and the power substation bus (:503) - plus a shared Flask
  operator HMI on :8093 (login portal, default creds `operator`/`operator`,
  read-only status pulled live off the datastores). A 0.3 s scan loop runs the
  golden control program; in the hardened build (`MODBUS_WRITE_OPEN=0`) it
  re-asserts the safe state every pass so an attacker's write gets stomped.
- `simmap/icsloops.py` + `models/{water,power}.py`: simmap is now a Modbus
  *client* to `field-plc`. Two loops read the coils/setpoints, step a coarse
  first-order model (`WaterModel`, `PowerModel`), write the PVs back so the HMI
  stays live, and mirror the derived state into `TownState`. The water/power
  subsystems are taken off the built-in idle physics.
- The exploits: an unauthenticated Modbus write. Stop the high-lift pump and
  the distribution pressure bleeds to zero within a few ticks - houses go dry
  on the map. Open a feeder breaker and that zone goes dark; open the main and
  the whole town does, with the bus frequency diving. Each plant's flag sits in
  an input-register block (IR 100+) that only populates when you set the
  maintenance-mode coil, so you have to interact with the PLC to read it.
- `scoring/flags.py`: `water_modbus_pump` and `power_modbus_feeder` (base 175,
  severity `loud`); the flag drops onto `pkt-flags` for `field-plc` to plant.
  A valid submission scores + raises Alert heat; the physical damage was
  already the player's write, so the map effect is a no-op.
- `player`: `recon.py` (guarded nmap sweep) and `modbus_attack.py`
  (`water stop-pump|dose-off|flag|restore`, `power trip <feeder>|trip-main|flag|
  restore`). `pymodbus` added to the image.
- Debug menu + reset now poke the real PLCs over Modbus, so the buttons and a
  genuine attack do the exact same thing; `pkt/reset {scope:water|power}`
  writes the golden coils/setpoints back.
- Map: the treated-effluent line from the sewage plant to the river is now a
  moving blue flow that turns algae-green when the treatment is bypassed; the
  river washes green with it. `simmap` gained `pymodbus`; phase badge -> 2.
- Verified from the `player` box: `modbus_attack.py water stop-pump` +
  `power trip industrial` -> houses dry, feeder dark, frequency 60 -> 59.3;
  flags extracted via the maint block; submitted for +394 and +492 (the second
  picks up the chain bonus for a second `utility` technique in the run);
  `restore` brings both back.

### Phase 1 - vertical slice: the General Store end to end
- `websites` (PHP 8 + Apache): the General Store behind a login portal styled
  after the Cross Creek HMI logons and Widgetorium's `login.php`. Seeded account
  `shopper` / `shopper`, plus registration (parameterised, safe). The scored bug
  is a real concatenated-`LIKE` SQL injection in the authenticated product
  search (`search.php`), 3 columns for a clean UNION, verbose SQL errors, and
  reflected XSS on the search term. Lifted from `widgetorium/webapp/src/`.
- `db` (MariaDB 11): the `generalstore` schema + seed, and `staff_notes` where
  the session flag lands (planted by the websites entrypoint after boot; no
  page, only reachable via `UNION SELECT 1,note,1 FROM staff_notes`).
- `scoring` built out: per-session flag generation + injection onto the shared
  `pkt-flags` volume (`flags.py`); HMAC signed-cookie sessions + scrypt
  (`auth.py`, ported from `webterm-3270-saas/auth/`); `POST /api/score/`
  `register` / `login` / `logout` / `run` / `arm` / `submit`, `GET /me` and
  `/leaderboard`; the score formula (`base x (1+stealth) x (1+chain) x speed`,
  `score.py`); one accepted flag per (run, technique); a valid submission
  publishes `pkt/score/events` and simmap breaks that shop.
- `player`: the boxed-in attacker box (sqlmap, nmap, curl, jq), default route
  dropped, `targets.py` lab-only guard.
- Map UI: player login / register, a run panel, a live leaderboard, and a
  target side-panel - clicking the General Store opens its portal in an iframe
  with a flag-submission box.
- Verified end to end: `sqlmap`/UNION out of the search -> flag -> submit ->
  +338, General Store shows `db_dumped` on the map, alert +1, leaderboard
  updates; dup and wrong-flag submissions rejected; `status.sh` audit clean.

### Phase 0 - scaffold
- Repo skeleton, GPL-3.0 licence, game-style README.
- Lifecycle scripts (`setup`, `start`, `stop`, `status`, `reset`) and `lib.sh`
  with the loopback-only guard and the `dc()` compose shim, adapted from
  Cross Creek.
- `docker-compose.yml` with `gateway` (nginx), `simmap` (Flask + flask-sock),
  `scoring` (Flask), and `bus` (Mosquitto, event bus and traffic-light target),
  on `edge-net` plus the internal `it-net` and `bus-net`.
- `simmap`: the town state model (8 storefronts + bank + police + fire + Town
  Hall + utilities + traffic + rail + alert), a 1 s tick loop, a coarse
  idle/degradation physics pass, an MQTT bridge, a WebSocket feed with
  full-snapshot-on-connect and `state_seq`, and the map UI: a pixel-art
  isometric base image with a calibrated live SVG overlay (`overlay.json`),
  a light/playful palette, a reset panel, a debug breach menu, and a
  dismissable donation banner ($britleywren).
- `scoring`: schema, health check, and stub `/api/score/*` endpoints.
- `docs/architecture.md` first cut.

### Design refresh (post-Phase-0)
- Renamed the project **Packet Creek -> Packet River** (repo, town, river, flag
  prefix `PKTR{}`), matching the reference art's welcome sign ("pop. 646").
- Map direction: pixel-art isometric base + live overlay, light palette (not
  control-room black). Every target's front door is a login portal, Cross Creek
  / Widgetorium style.
- Added to the plan: First Packet Bank & Trust as its own target district
  (online banking JWT `none` + account IDOR + ATM + a grid-tied alarm panel);
  Police + Fire as minor targets; Cinema + Bakery as set dressing; the nine
  named Main Street stores with one bug class each; a new **Diner Wi-Fi**
  network-attack lane (`netlab`, Phase 5). Build plan is now seven phases (0-6).
