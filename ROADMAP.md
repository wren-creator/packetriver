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
  beat your best. Overlay alignment gets a drag-and-copy editor
  (`?edit=1`, see `docs/overlay-editing.md`); a final pass waits for the
  Phase 6 art.
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
  - [x] **3d** IBM z16 behind the Bank: green-screen TN3270E + a RACF command
    family (`LISTUSER` / `RLIST` / `SETROPTS`), three curated findings -
    never-revoked `IBMUSER` with `SPECIAL`, `BANK.XFER.APPROVE` `UACC(READ)` +
    `WARNING` mode, `NOPROTECTALL`; flag in the profile's `INSTALLATION DATA`.
    Player-side client `z16_3270.py` (built - no arm64 `x3270`). A CICS
    inquiry / CEMT lane and a full interactive in-browser 3270 stay follow-ups.
- [x] **Phase 4 - Sewage + traffic + rail + Alert Level + blue team.**
  Sewage as a 4th `field-plc` Modbus PLC (`sewage_modbus`); `traffic-plc`
  commanded over the open MQTT bus (`traffic_mqtt`); `rail-plc` with a
  raw-TCP console + command injection (`rail_console`); the derail into the
  factory. The leaky-bucket Alert meter with hysteresis + `blueteam.py`
  (L2 credential rotation that actually bites, L5 auto-restore) + `logtail.py`
  turning scan noise into heat. `docker-compose.segmented.yml` +
  `bus/*.segmented` (authenticated broker with per-topic ACLs, all weaknesses
  off).
  - [x] Segmented build extended: `JWT_STRICT` (bank rejects `alg:none`),
    `RECEIPT_AUTH` (paygw), `MOCK_AS400_HARDENED` (blank sign-on rejected),
    `MOCK_Z16_HARDENED` (IBMUSER revoked), Phase 5 lane overrides (`NETLAB_TLS`
    encrypts the Diner portal + mail, `WAN_ADMIN=0` + rotated `ADMIN_PASS` +
    `PORTAL_TLS` on the SOHO router). Also fixed the segmented `bus`
    healthcheck (it published anonymously to an auth-required broker).
  - [ ] Deeper mainframe hardening: rotate QSECOFR, `*PUBLIC *EXCLUDE` on the
    payroll library, take the RACF profile out of WARNING / `UACC(NONE)`.
  - [ ] Campaign codes (Phase 6, EPUB-tied).
  - [ ] A real span-port IDS. A Suricata container on a Docker bridge only
    sees its own + broadcast traffic; an inline sensor that actually catches
    the Modbus writes / MQTT publishes / the AXFR needs a mirror interface or
    a router container. Today the counter-detection story is `logtail.py` +
    the broker ACLs + the field-plc golden re-assert.
- [x] **Recon layer - give every target a name (`*.packetriver.range`).**
  A `dns` container (CoreDNS) is the `player` box's only resolver, authoritative
  for `packetriver.range` and forwarding everything else to Docker's embedded
  DNS. Names are CNAMEs onto the container network, so `dig` / `nslookup` /
  `nmap water.packetriver.range` all work and recon is by business name
  (`firstpacketbank.packetriver.range`, `water.packetriver.range`, ...).
  - The zone is **deliberately AXFR-able** - `recon.py dns` (or `dig axfr
    packetriver.range @dns`) dumps the whole town, including a stray TXT record
    from a "decommissioned" box that carries the `dns_axfr` flag. TXT
    breadcrumbs (`_recon`, `_zone`) season it. Players start with only the
    resolver IP (wired via compose `dns:`).
  - **Official-sounding names** applied: HMI portal titles, the traffic-plc /
    rail-plc portal headers, the map hover labels, and the zone-file comments
    all use one municipal / corporate scheme ("Packet River Municipal Water
    Authority", "Packet River Power & Light", "Packet River & Southern Railroad
    - Dispatch", ...). See `docs/districts/recon.md` for the full table.
  - **No cross-portal navigation.** The field-plc HMI `<nav>` no longer links
    sibling plants and `GET /` no longer lists the four portals (returns 404).
    You land on each item independently, from the map or from recon by name.
  - [x] `gateway` real `Host:`-header vhost routing. The shop / civic CNAMEs
    point at `packetriver-gateway` now; nginx routes each `<shop>.packetriver.range`
    to its subdir of the shared `websites` container and hands each a distinct
    `Server` / `X-Powered-By` (`map $host ...`). An unknown `*.packetriver.range`
    gets the map. (The backend's own 404 page still leaks `Apache` - per-vhost
    ErrorDocument is a smaller follow-up.)
  - [x] PTR / reverse-DNS. `dns` resolves each container's it-net address at
    boot and serves an AXFR-able `20.31.172.in-addr.arpa` reverse zone;
    `recon.py rev` sweeps it. Boot-time snapshot (a container restart needs a
    `dns` rebuild).
  - [x] A mock corporate directory + toy whois: `/directory` and
    `/whois?q=` on the map server list every official name and its hostname.
    `.local` stays out (mDNS conflict on macOS).
- [x] **Phase 5 - Network-attack lanes (a different skill from web exploits).**
  - [x] **5a - The Diner Wi-Fi lane.** `netlab` (AP: cleartext rewards portal +
    toy POP3) + `netlab-patron` (a bot that logs in and reads mail in the
    clear) on an internal `lan-net`. `player` gains `tcpdump` + `dsniff`,
    `NET_RAW`, and `net.ipv4.ip_forward=1` (compose `sysctls`, not
    privileged); `wifi_sniff.py` runs an `arpspoof` MITM and pulls the flag
    from the patron's inbox. `netlab` watches its ARP cache for a MAC flip and
    publishes an Alert-heat event, so a sustained spoof crosses L1. Technique
    `diner_wifi` (base 125) -> Diner `carded`.
  - [x] **5b - The SOHO router pivot (residential -> rail).** `soho-router`
    (consumer router: WAN-side admin, `admin`/`admin`, a Diagnostics
    packet-capture returning a decoded text dump) + `soho-resident` (a rail
    engineer signing in to a cleartext crew portal on a loop) on an internal
    `home-net`. `soho_pcap.py`: default creds -> capture -> the flag (an
    `X-Reconcile` header) + the crew credential, which is reused on
    `rail-plc:2323` (a second static operator account) to chain into
    `rail_console` and throw the switch. Technique `soho_router_pcap` (base
    150, `noop`).
  - [ ] Follow-ups: hardened overrides in `docker-compose.segmented.yml` (TLS
    the portals, rotate the router creds, block residential -> OT); a
    dwell-time "patience" scoring bonus for 5b that ties into the stealth
    multiplier.
- [ ] **Phase 6 - EPUB, docs, art, polish.** Remaining: "Packet River 101" EPUB
  (chapters 1:1 with scenarios) with cover art, the ZAP automation plan
  (`docs/zap/`), the final pixel-art base image, README to its final
  game-page form with a labelled map screenshot.
  - [x] `docs/scenarios.md` + `scenarios-trainee.md` (Cross Creek shape:
    where / real-world / MITRE / confirm-with / physical consequence / fix;
    trainee = fix stripped), all 26 techniques.
  - [x] `docs/verification.md` (Section A containment / B per-technique /
    C reset / D defended / E ebook).
  - [x] `docs/districts/bank.md` + `docs/districts/civic.md` +
    `docs/districts/recon.md`; `architecture.md` brought current.
  - [x] `instructor/ctf/check-flags.sh` + `answers.txt` - smoke-tests the
    mint -> plant -> submit -> score loop for all 26 (currently 26 ok).
  - **Guidance, not walkthroughs** (see `docs/learning-design.md`). The
    game must not ship a copy-paste path to controlling the town in 30
    minutes.
    - [x] `scoring/flags.py` `hint` strings audited to Tier-1 direction; the
      sharp step-by-step moved to `instructor/answer-key.md`.
    - [x] `docs/districts/*.md` audited to Tier-1 (bug class / tool / effect /
      fix, no payloads / params / creds / flag locations); the two spills in
      `docs/architecture.md` scrubbed too. Sharp version lives in
      `instructor/answer-key.md`.
    - [ ] Each future district doc + `flags.py` entry ships Tier-1 from the
      start; the answer-key entry lands in the same commit.
  - [ ] **Easter-egg hints.** Hide help as in-world artifacts (a stale
    `README.old`, a `.bak` config, a `robots.txt`, a note baked into a
    texture, an NPC line). Each egg gives a *fragment* - a technique name, one
    parameter, one fact, a blanked payload skeleton - never a finished
    command. Optional, lightly score-rewarded, tunable via
    `PKT_EGGS=off|subtle|obvious`.

## Ideas / bucket list

- **Credential hygiene, deeper.** The field-plc HMI logins are now per-plant,
  minted at boot, rotated at Alert L2, discoverable via `/ops/handover.txt`.
  Next: (a) a wall-clock rotation option (`PKT_CRED_ROTATE_MIN`, off by
  default - a timer that rotates mid-run is a frustration/CI trap, so it stays
  opt-in); (b) cross-service credential leakage - bury one plant's HMI cred in
  the drycleaner `.git` history or the police `config.json` so it becomes a
  chain; (c) the "credential IS the bug" logins (`QSECOFR`, `IBMUSER`, the shop
  defaults) stay static on purpose - a never-rotated default is the lesson.
- **Midrange + mainframe tier.** Give the big civic systems the machines a
  real small town would run them on:
  - [x] an **AS/400 (IBM i)** behind **City Hall** and the **Widget Factory**,
    running payroll (TN5250 green screen). Landed in Phase 3c. Remaining depth:
    a runnable RPG IV / DDS payroll app (the `rpg/` interpreter is vendored but
    the payroll path is SQL-only today), library-list / command-line injection.
    (Interactive green screen already works via web3270's Manual Connection at
    `host.docker.internal:8992` - see `docs/districts/mainframe.md`; vendoring
    `session.js` into the map panel is the remaining polish.)
  - [x] an **IBM z16** behind **First Packet Bank & Trust** for core banking
    (TN3270E, z/OS, RACF). Landed in Phase 3d - a RACF command family with
    three curated findings. Remaining depth: CICS transaction abuse
    (CEMT/CECI), APF / the writable-APF-library escalation the mock's `LISTAPF`
    already hints at, TSO REXX, surrogat, and a full interactive in-browser
    3270 instead of the built client.
  Both tie into the web front doors: pop the City Hall payroll portal then
  pivot to the AS/400; pop the bank's online banking then pivot to the z16.
- [x] **Widget Factory PLC controls.** Assembly line (conveyor run/stop, line
  speed, e-stop interlock) + train loading (gantry / hopper gate /
  car-in-position) on `field-plc` :504. Landed in Phase 3b.
  - [x] A car being loaded (hopper gate open) when the train derails onto the
    spur is now a pile-up: throughput hard-zeros and the line jams on top of
    the fire.
- [x] Widget Factory ops site (weak SNMP). `factory-snmp` is a real net-snmp
  agent with the shipped community strings - `public` reads the
  line-management subtree (the `factory_snmp` flag is an OID), a read-write
  community `snmpset`s the line-enable OID and stops the line
  (`pkt/factory/cmd` -> simmap). Hardened: `SNMP_HARDENED=1` drops the write
  community and moves the read community off `public`.
- [x] `ttyd` browser terminal in the `player` box - added in Phase 3c (the map's
  "green screen ↗" link on Town Hall opens it).
- [x] Timed events. `PKT_EVENTS=off|calm|lively` drives a news crew (loud
  incidents on camera hit Alert heat 1.6x), a state inspector (an incident
  during the visit = a citation + 45 heat), and a Founder's Day parade (a
  signal hijack during the parade racks crashes ~4x faster). Snapshot `events`
  block, `pkt/sim/event/*`, `POST /api/debug/event` to fire one on demand. See
  `docs/districts/timed-events.md`.
- [ ] Closer-to-real RF for the Wi-Fi lane would be its own wireless range, not
  this repo.

## Related work in the sibling repos

- [ ] **Widgetorium and Cross Creek: add a donation banner page.** Give each of
  the sibling ranges the same corner tip-jar banner Packet River has (dismissable,
  `localStorage`, points at the CashApp cashtag, never gates anything). Tracked
  here so it does not get lost; do the actual work in those repos.
