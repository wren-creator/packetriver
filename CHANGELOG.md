# Changelog

All notable changes to Packet River. Newest first.

## [Unreleased]

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
