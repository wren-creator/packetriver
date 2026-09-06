# Roadmap

Six phases. Phase 1 is a true vertical slice (one district, whole loop end to
end); each later phase widens the town with real depth. Full plan and the
reuse map live in the design doc.

- [x] **Phase 0 - Skeleton & lifecycle.** Repo scaffold, licence, README,
  lifecycle scripts + loopback guard, compose skeleton (gateway, simmap,
  scoring, bus), the live map with a debug breach/reset path, `docs/architecture.md`.
- [ ] **Phase 1 - Vertical slice.** One shop vhost with a real SQLi + verbose
  errors, `db`, per-session flag generation + injection, signed-cookie auth,
  `POST /api/score/{arm,submit}`, the score formula, the leaderboard, the
  `player` attacker box. Deliverable: sign up, `sqlmap` the shop, watch it
  break on the map, beat your best, reset it.
- [ ] **Phase 2 - Water + power districts.** `field-plc` (water + electric
  soft-PLCs), the physics integrators lifted from `crosscreek/process-sim`,
  Modbus/S7 attack scripts, houses that go dry and dark. Validate `python-snap7`
  / `cpppo` on arm64 here.
- [ ] **Phase 3 - Full Main Street + City Hall + payments + carding.** All 8
  shop vhosts (one bug class each), `paygw` fake gateway with test PANs, City
  Hall (announcements + payroll + LFI), the `websites` -> `ot-net` pivot.
- [ ] **Phase 4 - Sewage + traffic + rail + Alert Level + blue team.**
  `traffic-plc`, `rail-plc`, sewage on `field-plc`, the river + swimmers, the
  leaky-bucket Alert meter, the blue-team response (password rotation, rate
  limiting, segmentation), campaign codes, `docker-compose.segmented.yml`.
- [ ] **Phase 5 - EPUB, docs, polish.** "Packet Creek 101" EPUB (chapters 1:1
  with scenarios), `docs/scenarios.md` + `scenarios-trainee.md`,
  `docs/verification.md`, the CTF flag-check script, the ZAP automation plan,
  README to its final game-page form with a labelled map screenshot.

## Ideas / bucket list

- [ ] Widget Factory ops site (weak SNMP) instead of the factory being a pure
  consequence entity.
- [ ] Optional `ttyd` browser terminal in the `player` box for players without
  a local shell.
- [ ] Timed events beyond the news crew: a state inspector visit, a Founder's
  Day parade that fills the crossroads.

## Related work in the sibling repos

- [ ] **Widgetorium and Cross Creek: add a donation banner page.** Give each of
  the sibling ranges the same corner tip-jar banner Packet Creek has (dismissable,
  `localStorage`, points at the CashApp cashtag, never gates anything). Tracked
  here so it does not get lost; do the actual work in those repos.
