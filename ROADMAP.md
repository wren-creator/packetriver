# Roadmap

Seven phases. Phase 1 is a true vertical slice (one district, whole loop end to
end); each later phase widens the town with real depth. Full plan and the
reuse map live in the design doc.

- [x] **Phase 0 - Skeleton & lifecycle.** Repo scaffold, licence, README,
  lifecycle scripts + loopback guard, compose skeleton (gateway, simmap,
  scoring, bus), the pixel-art live map + overlay with a debug breach/reset
  path, `docs/architecture.md`.
- [ ] **Phase 1 - Vertical slice.** The General Store behind a login portal:
  real SQLi + verbose errors, `db`, per-session flag generation + injection,
  signed-cookie auth, `POST /api/score/{arm,submit}`, the score formula, the
  leaderboard, the `player` attacker box. Deliverable: sign up, `sqlmap` past
  the portal, watch the shop break on the map, beat your best, reset it.
- [ ] **Phase 2 - Water + power districts.** `field-plc` (water + electric
  soft-PLCs), the physics integrators lifted from `crosscreek/process-sim`,
  Modbus/S7 attack scripts, houses that go dry and dark. Validate `python-snap7`
  / `cpppo` on arm64 here.
- [ ] **Phase 3 - Full Main Street + Town Hall + payments + the Bank.** All 8
  storefronts (one bug class each) behind login portals, `paygw` fake gateway
  with test PANs, Town Hall (announcements + payroll + LFI), the **`bank`**
  service (JWT `none`, account IDOR, ATM, grid-tied alarm), Police + Fire as
  minor targets, the `websites` -> `ot-net` pivot.
- [ ] **Phase 4 - Sewage + traffic + rail + Alert Level + blue team.**
  `traffic-plc`, `rail-plc`, sewage on `field-plc`, the river + swimmers +
  swimming beach, the leaky-bucket Alert meter, the blue-team response
  (password rotation, rate limiting, segmentation), campaign codes,
  `docker-compose.segmented.yml`.
- [ ] **Phase 5 - The Diner Wi-Fi lane.** `netlab`: a mock open AP, a captive
  portal, cleartext services on a sniffable segment; `player` gets `tcpdump` +
  a sniff/MITM script. A different skill from web exploits. Honest scope: a
  sniffable LAN standing in for 802.11, not real radio.
- [ ] **Phase 6 - EPUB, docs, art, polish.** "Packet River 101" EPUB (chapters
  1:1 with scenarios), `docs/scenarios.md` + `scenarios-trainee.md`,
  `docs/verification.md`, the CTF flag-check script, the ZAP automation plan,
  the final pixel-art base image, README to its final game-page form with a
  labelled map screenshot.

## Ideas / bucket list

- [ ] Widget Factory ops site (weak SNMP) instead of the factory being a pure
  consequence entity.
- [ ] Optional `ttyd` browser terminal in the `player` box for players without
  a local shell.
- [ ] Timed events beyond the news crew: a state inspector visit, a Founder's
  Day parade that fills the crossroads.
- [ ] Closer-to-real RF for the Wi-Fi lane would be its own wireless range, not
  this repo.

## Related work in the sibling repos

- [ ] **Widgetorium and Cross Creek: add a donation banner page.** Give each of
  the sibling ranges the same corner tip-jar banner Packet River has (dismissable,
  `localStorage`, points at the CashApp cashtag, never gates anything). Tracked
  here so it does not get lost; do the actual work in those repos.
