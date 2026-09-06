# Changelog

All notable changes to Packet River. Newest first.

## [Unreleased]

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
