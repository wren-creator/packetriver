# Roadmap

Seven phases. Phase 1 is a true vertical slice (one district, whole loop end to
end); each later phase widens the town with real depth. Full plan and the
reuse map live in the design doc.

- [x] **Phase 0 - Skeleton & lifecycle.** Repo scaffold, licence, README,
  lifecycle scripts + loopback guard, compose skeleton (gateway, simmap,
  scoring, bus), the pixel-art live map + overlay with a debug breach/reset
  path, `docs/architecture.md`.
- [x] **Phase 1 - Vertical slice.** The General Store behind a login portal:
  real concatenated-`LIKE` SQLi + verbose errors + reflected XSS in the search,
  `db` (MariaDB), per-session flag generation + injection, HMAC signed-cookie
  auth + scrypt, `POST /api/score/{register,login,run,arm,submit}` + `/me` +
  `/leaderboard`, the score formula, the live leaderboard, the target
  side-panel, the boxed-in `player` box. Sign up, get a shop session, UNION the
  flag out of the search, submit it, watch the store break on the map (+alert),
  beat your best. Overlay alignment still rough - tweak later.
- [x] **Phase 2 - Water + power districts.** `field-plc` runs two real
  Modbus/TCP soft-PLCs (water :502, power :503) plus a shared operator HMI
  (`operator`/`operator`). simmap drives the physics from them via `icsloops`
  (`WaterModel` / `PowerModel`). Unauth Modbus writes: stop the high-lift pump
  -> the town loses water; open a feeder breaker -> a zone goes dark; open the
  main -> whole town dark, frequency dives. Flag per plant in an input-register
  block that fills when you set the maintenance-mode coil. `player` gets
  `recon.py` + `modbus_attack.py`. Debug buttons and reset now poke the real
  PLCs, so they do the same thing an attack does. (Modbus for power too, not S7
  - arm64-safe; an S7/CIP "vendor dialects" pass can come later.)
- **Phase 3 - Full Main Street + Town Hall + payments + the Bank + mainframes.**
  Split into ordered sub-phases, each committed + playable:
  - [x] **3a-1** all 8 storefronts, one bug class each (IDOR, auth-bypass,
    exposed backup, stored XSS + regex bot, default creds, `.git` leak, SSRF).
  - [x] **3a-2** Town Hall (announcements deface, payroll portal, LFI) +
    Police + Fire as minor targets + `paygw` (fake card gateway, test PANs) +
    a real checkout on the shops.
  - [x] **3a-3** the Bank district (`bank` service: JWT `none`, account IDOR,
    staff dashboard leaking the wire token, alarm panel on the business feeder).
  - [x] **3b** Widget Factory PLC controls (assembly line + train loading) on
    `field-plc` (Modbus/TCP :504, `FactoryModel`).
  - [x] **3c** AS/400 (IBM i) behind City Hall + the factory for payroll:
    green-screen TN5250, three stacked IBM i bugs (blank sign-on, default
    `QSECOFR`, `PAYROLL` library `*PUBLIC *ALL`); flag pulled via `STRSQL`.
    Player-side client `as400_5250.py` (built - no arm64 `tn5250`). A full
    interactive in-browser 5250 (web3270 `session.js`) stays a follow-up.
  - [ ] **3d** IBM z16 behind the Bank: green-screen TN3270 + a CICS inquiry +
    a RACF panel + curated bugs (UACC, WARNING mode, magic SVC). Reuse
    `web3270` mock LPARs.
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

- **Midrange + mainframe tier.** Give the big civic systems the machines a
  real small town would run them on:
  - [x] an **AS/400 (IBM i)** behind **City Hall** and the **Widget Factory**,
    running payroll (TN5250 green screen). Landed in Phase 3c. Remaining depth:
    a runnable RPG IV / DDS payroll app (the `rpg/` interpreter is vendored but
    the payroll path is SQL-only today), library-list / command-line injection,
    and a full interactive in-browser 5250 (web3270 `session.js` behind a Node
    renderer) instead of the built extraction client.
  - [ ] an **IBM z16** behind **First Packet Bank & Trust** for core banking
    (TN3270, z/OS, RACF, CICS) - Phase 3d. Reuse the mock-LPAR / TN3270 stack
    from `web3270`. Bugs: RACF misconfig (universal access, WARNING mode, magic
    SVC), CICS transaction abuse, APF / surrogat, TSO REXX. This is Britley's
    home turf and the range's real differentiator.
  Both tie into the web front doors: pop the City Hall payroll portal then
  pivot to the AS/400; pop the bank's online banking then pivot to the z16.
- [x] **Widget Factory PLC controls.** Assembly line (conveyor run/stop, line
  speed, e-stop interlock) + train loading (gantry / hopper gate /
  car-in-position) on `field-plc` :504. Landed in Phase 3b. Still open: tying a
  car-loaded-while-the-switch-is-thrown to the rail district (Phase 4).
- [ ] Widget Factory ops site (weak SNMP) alongside the PLC controls, instead of
  the factory being a pure consequence entity.
- [x] `ttyd` browser terminal in the `player` box - added in Phase 3c (the map's
  "green screen ↗" link on Town Hall opens it).
- [ ] Timed events beyond the news crew: a state inspector visit, a Founder's
  Day parade that fills the crossroads.
- [ ] Closer-to-real RF for the Wi-Fi lane would be its own wireless range, not
  this repo.

## Related work in the sibling repos

- [ ] **Widgetorium and Cross Creek: add a donation banner page.** Give each of
  the sibling ranges the same corner tip-jar banner Packet River has (dismissable,
  `localStorage`, points at the CashApp cashtag, never gates anything). Tracked
  here so it does not get lost; do the actual work in those repos.
