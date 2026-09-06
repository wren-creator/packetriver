# Changelog

All notable changes to Packet Creek. Newest first.

## [Unreleased]

### Phase 0 - scaffold
- Repo skeleton, GPL-3.0 licence, game-style README.
- Lifecycle scripts (`setup`, `start`, `stop`, `status`, `reset`) and `lib.sh`
  with the loopback-only guard and the `dc()` compose shim, adapted from
  Cross Creek.
- `docker-compose.yml` with `gateway` (nginx), `simmap` (Flask + flask-sock),
  `scoring` (Flask), and `bus` (Mosquitto, event bus and traffic-light target),
  on `edge-net` plus the internal `it-net` and `bus-net`.
- `simmap`: the town state model (~20 entities), a 1 s tick loop, a coarse
  idle/degradation physics pass, an MQTT bridge, a WebSocket feed with
  full-snapshot-on-connect and `state_seq`, and the inline-SVG map UI with a
  reset panel, a debug breach menu, and a dismissable donation banner.
- `scoring`: schema, health check, and stub `/api/score/*` endpoints.
- `docs/architecture.md` first cut.
