# Changelog

All notable changes to Packet River. Newest first.

## [Unreleased]

### Containment audit - the pivot-isolation check was a false alarm

- `status.sh`'s `player → traffic-plc` check fired `audit FAILED ... stop the
  town` on a healthy flat town. Two bugs: it probed port 8092 (traffic-plc
  listens on 8095, so the probe hit a closed port), and its exit-code test was
  inverted against the internet check right above it, so a *failed* connect
  landed in the `bad` branch. A properly segmented town would have failed it
  too.
- Fixed the port and the branch sense. The real gap it was meant to catch - no
  `ot-net`, so `player` shares `it-net` with the PLCs - is now one non-fatal
  `[!]` warn and `./status.sh` exits 0, matching `docs/verification.md` A1.
  Building real OT segmentation is now a tracked ROADMAP item.

### Portals ask for credentials again

- Every login portal (the shops, the field HMI, the bank, the SOHO router) now
  has a short idle timeout, `PKT_PORTAL_TTL` (default 180 s). Open a portal
  after a real gap and it presents the login form instead of dropping you
  straight onto the dashboard, so the login step is always part of the
  exercise. Active use keeps a session alive. The bank JWT `exp` follows the
  same TTL; the SOHO router cookie gets a matching `max-age`.

### "Packet River 101" - the syllabus EPUB

- `docs/syllabus-epub/` builds to `docs/Packet-River-101.epub`: nine sessions,
  one per district group (Main Street; civic + money + green screens; the
  utilities; recon + the network lanes; hardening; a capstone + IR tabletop;
  the author). Same "guidance not walkthroughs" register as the district docs -
  bug class, tool family, what you'll see, the fix, the real-world parallel,
  the MITRE mapping. The sharp step-by-step stays in
  `instructor/answer-key.md`. Generated cover art. `build-epub.sh` lifts the
  Cross Creek toolchain.

### z16 - APF escalation

- New `z16_apf` technique (base 250, loud). `LISTAPF` already flagged
  `USER.LOADLIB` as APF-authorised and writable; `LISTDS 'USER.LOADLIB'` now
  confirms the volume authority and `CALL 'USER.LOADLIB(<member>)'` runs
  authorised - the mock returns a key-0 / supervisor-state escalation token.
  Fires `bank_drain`, the same end state as the RACF and JWT paths. (The
  deeper mainframe depth - CICS CEMT/CECI, TSO REXX, a runnable RPG payroll
  app - stays on the roadmap.)

### Widget Works - a management plane

- New `factory-snmp` container: a real net-snmp agent with the shipped
  community strings. `public` reads the line-management subtree (the new
  `factory_snmp` flag, base 150, is an OID); a read-write community `snmpset`s
  the line-enable OID and stops the assembly line (`pkt/factory/cmd` ->
  simmap). Same end state as the Modbus path, a different plane. `player` gains
  the net-snmp clients and `snmp_attack.py`. Hardened: `SNMP_HARDENED=1`.
- A rail car being loaded (hopper gate open) when the train derails onto the
  spur is now a pile-up - throughput hard-zeros and the line jams on top of
  the fire. Time the `rail_console` derail against the loading cycle.

### Recon layer - the deferred pieces

- **Real `Host:`-header vhost routing.** The shop and civic CNAMEs point at the
  gateway now. nginx routes each `<name>.packetriver.range` to its subdir of
  the shared `websites` container and gives each a distinct `Server` /
  `X-Powered-By`, so app-layer fingerprinting tells the shops apart even though
  they are one container. An unknown `*.packetriver.range` gets the map.
- **Reverse DNS.** `dns` resolves each container's it-net address at boot and
  serves an AXFR-able `20.31.172.in-addr.arpa` zone; `recon.py rev` sweeps it.
- **Corporate directory + whois.** `/directory` and `/whois?q=` on the map
  server list every official name and its hostname.

### Segmented build - coverage extended

- `docker-compose.segmented.yml` now hardens the web tier and the Phase 5
  lanes, not just the OT / broker weaknesses:
  - `JWT_STRICT` - the bank rejects `alg:none` and pins HS256.
  - `RECEIPT_AUTH` - the card gateway requires a bearer token on `/receipt`.
  - `MOCK_AS400_HARDENED` (blank sign-on rejected) / `MOCK_Z16_HARDENED`
    (the never-revoked IBMUSER is revoked). Deeper RACF / library-authority
    hardening stays on the roadmap.
  - `NETLAB_TLS` - the Diner portal goes HTTPS and mail goes POP3S, so the
    MITM only sees ciphertext. `WAN_ADMIN=0` + a rotated `ADMIN_PASS` +
    `PORTAL_TLS` on the SOHO router: admin is off the WAN interface, the
    default is dead, and the capture is opaque.
- Fixed the segmented `bus` healthcheck: it published anonymously to a broker
  that now requires auth, so the container reported unhealthy and took
  simmap / scoring down with it. It authenticates as `simmap` now.
- A real span-port IDS is still open (see ROADMAP - a bridge can't tap another
  container's traffic without a topology change).

### Timed events

- `PKT_EVENTS=off|calm|lively` gives the town a clock. A **news crew** parks at
  whatever's most broken and any Alert heat from an incident on that subsystem
  is multiplied by 1.6 while they film. A **state inspector** visits on a
  timer, and an incident that's active when they leave costs +45 heat and a
  citation (an incident you started during the visit is worst-case; one you
  cleaned up costs nothing). A **Founder's Day parade** fills the crossroads,
  and a signal hijacked to ALL-GREEN during it racks up crashes about 4x as
  fast. Snapshot `events` block, `pkt/sim/event/*`, `POST /api/debug/event`,
  a HUD pill and a camera marker on the map. `docs/districts/timed-events.md`.

### Phase 5 — network-attack lanes

- **Diner open Wi-Fi (`diner_wifi`, base 125).** New internal `lan-net`.
  `netlab` serves a cleartext rewards portal + a toy POP3; `netlab-patron`
  signs in and reads mail over the segment on a loop. A switch won't flood
  their unicast to you, so `wifi_sniff.py` runs an `arpspoof` MITM (`player`
  gains `tcpdump` + `dsniff`, `NET_RAW`, and `net.ipv4.ip_forward=1` via
  compose `sysctls`, no privileged) and pulls the flag from the patron's
  inbox. `netlab` watches its ARP cache and feeds Alert heat on a MAC flip,
  so a sustained spoof crosses Level 1. Submitting flips the Diner to
  `carded`. Honest scope: a sniffable LAN standing in for open 802.11.
- **SOHO router pivot (`soho_router_pcap`, base 150).** New internal
  `home-net`. `soho-router` is a consumer router with WAN-side admin still on
  `admin/admin` and a Diagnostics packet-capture that returns a decoded dump;
  `soho-resident` (a rail engineer) signs in to a cleartext crew portal on a
  loop. `soho_pcap.py` reads the flag and the crew credential out of the
  capture; the credential is reused on `rail-plc:2323` (a second static
  operator account) to chain into `rail_console` and throw the switch — the
  residential-to-OT pivot.
- Docs: `docs/districts/diner-wifi.md`, `docs/districts/soho-router.md`,
  a Group F in `scenarios.md` / `scenarios-trainee.md`, verification Group F,
  answer-key "Network lanes", architecture + README + ROADMAP updated.
  `check-flags.sh`: 26 ok, 0 failed.

### Documentation pass

- `docs/scenarios.md` + `docs/scenarios-trainee.md`: all 24 techniques in the
  Cross Creek shape (where / real-world parallel / MITRE / confirm-with /
  physical consequence / fix). Trainee edition is the instructor edition with
  the fix stripped.
- `docs/verification.md`: the end-to-end runbook, with Section A containment,
  B per-technique, C reset, D defended re-run, E ebook.
- New district docs: `docs/districts/bank.md` (JWT `alg:none`, account IDOR),
  `docs/districts/civic.md` (Town Hall deface + LFI, Police, Fire, paygw IDOR).
  `main-street.md` now links them instead of promising them.
- `docs/architecture.md` brought current: the full 14-service list, the actual
  three-network layout (no `ot-net`), the recon layer, the spur-routing
  behaviour, HMI credential rotation, and the current anti-cheat posture.
- `instructor/ctf/check-flags.sh` + `answers.txt`: smoke-tests the
  mint → plant → submit → score loop for every technique (24 ok, 0 failed).
- Fixed stale reset-scope names in `civic.md` / `mainframe.md` (`cityhall` /
  `police` / `fire`, not a non-existent `civic` scope).

### Train runs the spur

- Routing the rail switch to `spur` before the train reaches the branch (under
  the "R" of "Main Rail Line") now routes the train *onto* the spur: it travels
  the spur polyline down to the Widget Factory over ~5 s, then derails into it.
  Before, it snapped straight to the factory and the branch point didn't line
  up with the painted spur. New `Rail.on_spur` / `spur_pos`; `SWITCH_POINT`
  retuned to the branch.

### Recon layer — every target has a name

- New `dns` container (CoreDNS) is the `player` box's only resolver: authoritative
  for `packetriver.range`, forwarding everything else to Docker's embedded DNS.
  Wired via compose `dns:` / `dns_search:`, so the attacker box starts with just
  a resolver IP and works the town by business name
  (`nmap water.packetriver.range`, `curl firstpacketbank.packetriver.range`).
  Names are CNAMEs onto the container network so lookups follow through.
- The zone **answers AXFR from anyone**, a new low-value `dns_axfr` recon
  technique (base 75, `quiet`). `recon.py dns` (or `dig axfr packetriver.range
  @dns`) dumps every host plus a stray TXT record from a "decommissioned" box
  that carries this run's flag. `_recon` / `_zone` TXT breadcrumbs season it.
  `recon.py` now runs the DNS sweep first; `player` image gains `dnsutils`.
- **Official-sounding names** applied across the board: HMI portal titles, the
  traffic-plc / rail-plc portal headers, the map hover labels, and the
  zone-file comments now use one municipal / corporate scheme. Full table in
  `docs/districts/recon.md`.
- **No cross-portal navigation**: the field-plc HMI `<nav>` no longer links the
  other three plants, and `GET /` on `field-plc:8093` no longer lists the
  portals (returns 404). You land on each target independently.
- Still open (tracked in `ROADMAP.md`): `gateway` real `Host:`-header vhost
  routing so the 8 shops get distinct `Server` / 404 fingerprints; PTR / reverse
  sweep; a mock whois / corporate directory.

### Map pass before going public

- **Sewage contamination visual**: the full-height green river wash is gone.
  It's now a blocky "pixelated" mosaic over a draggable `beachZone` (beach
  edge across to the far bank), revealed as `river_contamination` climbs.
- **`houses` retired**: the 14 combined power-window + water-drop markers were
  redundant once `powerResidential` (31 yellow) and `waterResidential` (31
  blue) landed, and drew a double marker. Removed from the overlay, the render,
  the editor, the CSS, and the town snapshot.
- New distribution dot layers, each dimming with its feeder / main:
  `powerResidential` (31), `powerBusiness` (18), `powerPlant` (12),
  `waterResidential` (31); `streetlights` 11 -> 12 and lit white.
- Two new animated substation feeds: `powerFeederBiz` (downtown / Main Street)
  and `powerFeederPlant` (the Widget Factory). `waterMain` and `powerFeeder`
  densified to 7 vertices each; `railPath` 16 -> 19; the spur is a 4-point
  `spurPath` polyline.
- `?edit=1` editor: handles now render in the live map colour of what they
  edit (with a legend), and `beachZone` / `spurPath` / the new dot layers are
  all draggable. Bigger, readable device labels on the plant mimics; the
  power / factory / sewage plant portals carry the town name.
- `overlay.json` re-aligned against the base art with the editor.

### Per-plant HMI credentials + rotation

- The four field-plc SCADA HMIs no longer share `operator` / `operator`. Each
  plant has its own operator login, minted fresh at boot by a new
  `scoring/creds.py` into `/run/secret/creds/`. `field-plc` reads its own live
  per request (no restart needed), falling back to `HMI_USER`/`HMI_PASS` only
  if the vault isn't mounted.
- The current set is discoverable at `GET /ops/handover.txt` on `field-plc:8093`
  - an unauthenticated "shift handover" sheet, the kind an ops team leaves on
  the historian - so the answer key points at *where the creds live*, not at a
  value. It always reflects the latest rotation.
- Rotation: the blue team now publishes `pkt/creds/rotate` at Alert Level 2
  (alongside the existing traffic-PIN / rail-console rotation); `scoring`
  re-mints the set and rewrites the handover sheet. An in-progress attacker's
  saved HMI login stops working until a reset. Verified end to end.
- The "credential IS the bug" logins - AS/400 `QSECOFR`, z16 `IBMUSER`, the
  shop default creds - are deliberately left static; a never-rotated default
  is the whole lesson there. Wall-clock rotation (`PKT_CRED_ROTATE_MIN`) and
  cross-service credential leakage are roadmapped.
- The HMI login pages now signpost the bypass ("field bus in service -
  engineering writes accepted on Modbus/TCP 50x") so nobody rabbit-holes on
  the login.

### Field HMIs rebuilt as vendor mimic panels

- Each of the four field plants (`/water`, `/power`, `/factory`, `/sewage`)
  is now its own operator terminal: its own login page, its own session, and
  its own vendor theme (AQUAVIEW / GRIDMASTER / PLANTLINK / CLARUS) - they no
  longer share one combined status page.
- Cross Creek-style: a data-driven SVG P&ID mimic per plant (pipes, pumps,
  tanks with live fill, breakers, valves), live tag boxes that float above
  their tap point, clickable devices that open an AUTO/HAND + START/STOP
  faceplate, and a setpoints dialog. One renderer; each plant is a `PLANTS[]`
  entry.
- The HMI reads and writes the same Modbus datastores over authenticated
  routes (`/<plant>/api/state`, `/<plant>/api/cmd`) - verified: stopping the
  high-lift pump from the water HMI drains the town. HAND is a new HR block
  (`HAND_BASE=20`); in the segmented build the scan loop re-asserts golden
  state but skips HAND devices, while the unauthenticated Modbus attack -
  which never touches the HAND flags - still gets stomped.
- Fixed a pre-existing `(tuple).replace()` bug in the old factory HMI rows
  that 500'd the whole page.

### Phase 4 - Sewage + Traffic + Rail + Alert Level + blue team

**Three new OT exploit districts** (each verified end to end, flag -> submit ->
map degrades -> reset restores):

- **Sewage** (`sewage_modbus`, base 175): a 4th soft-PLC on `field-plc`
  (`:505` / host `:5505`) - aeration, disinfection dosing, treated-return
  pump, storm-bypass gate. Unauth Modbus writes open the bypass or stop
  aeration; `effluent_path` flips to raw, the outfall goes algae-green, the
  river plume ramps and the swimmers sicken. `models/sewage.py`, an icsloops
  sewage loop, a Sewage Treatment panel on the HMI, `modbus_attack.py sewage`.
- **Traffic** (`traffic_mqtt`, base 175): `traffic-plc`, five signal
  controllers that take their commanded mode off the bus. `pkt/traffic/<id>/set`
  has no ACL and no auth on the flat broker; publish to it and a crossroads
  locks ALL-GREEN. `pkt/traffic/eng` takes a PIN and coughs up the flag (a
  live, non-retained reply). `traffic_attack.py`; player image gains
  `mosquitto-clients`.
- **Rail** (`rail_console`, base 200): `rail-plc`, the loop/spur switch
  controller with a raw-TCP maintenance console on `:2323`. Default creds
  `maint/maint`, and `set label` concatenates operator input into a shell call
  (command injection). `set switch spur` throws the switch; simmap reads
  `pkt/rail/switch` and, when the train crosses the branch, derails it into the
  factory (fire). `rail_attack.py`.

**Alert Level + blue team:**

- The leaky-bucket Alert meter (`models/town.py`) gets downward hysteresis and
  a `blue_actions` list. `simmap/blueteam.py` runs on every level rise: L1 SOC
  banner, **L2 rotates the traffic PIN + rail console password** over
  `pkt/reset {scope:"creds"}` (an in-progress attacker's next canned command
  fails until a reset), L3/L4 banners, **L5 auto golden-restore of the
  worst-hit subsystem**. `pkt/alert/level` feeds `scoring`'s stealth bonus.
  The UI toasts each SOC action.
- `simmap/logtail.py` tails the gateway's JSON access log (shared volume) and
  turns scanner noise - tool user-agents, 4xx bursts, path sprays - into Alert
  heat, so a careless approach costs you even before you land anything.

**Segmented build:** `docker-compose.segmented.yml` + `bus/mosquitto.segmented.conf`
+ `acl.segmented` + `passwd.segmented`. `./start.sh --segmented` turns every
weakness off: `MODBUS_WRITE_OPEN=0`, an authenticated broker with per-topic
ACLs, rotated PIN / console creds / HMI password, verbose errors + weak
sessions off. Run the same attacks, watch them fail. (Web-tier and mainframe
hardening flags are a follow-up.)

- `scoring/flags.py`: `sewage_modbus`, `traffic_mqtt`, `rail_console`.
  `/api/config` phase -> 4. `.env.example` gains the PIN + console creds.
- Reset panel `sewage` / `traffic` / `rail` scopes restore their district
  (and any rotated creds).
- `docs/districts/{sewage,traffic,rail}.md`, answer-key entries.
- Campaign codes (the EPUB practice-mode hook) are deferred to Phase 6.

### Map alignment pass + a feed-stability fix
- The `/ws` feed no longer pulses live/down: `simmap` was on
  `GeventWebSocketWorker` while flask-sock does its own WS framing, and the two
  framers on one socket made the browser reconnect every few seconds. Now on
  the plain `-k gevent` worker, no `ping_interval`, `gevent-websocket` dropped.
- `overlay.json` aligned against the base art with the new `?edit=1` editor:
  every building box, the flows, the river, houses, streetlights.
- New on the map: a **Railroad Control** building (SE of the Police Station,
  `kind: rail`, wired in Phase 4), 6 more houses (8 -> 14) and 5 more
  streetlights, a 5th crossroads, and ~2x the rail-line vertices for curves.
- Traffic signals are one dot per crossroads now, green-weighted (6 s green
  each way, 2 s all-red on the change), the corners seeded out of phase so
  they don't all blink at once; hijack still locks solid green.
- The train sprite is +3 px across the track (not longer) so it reads better.

### Overlay editor (`?edit=1`)
- `simmap/web/edit.js`: a drag-and-copy editor for `overlay.json`. Loads for
  everyone, inert without `?edit=1` on the URL, so players never see it. With
  it on: a draggable handle for every coordinate (building centres + size,
  intersections, houses, streetlights, rail path, river, swimmers, the two
  utility flows, spur points), a 5% / 2.5% calibration grid, a live cursor
  fraction readout, arrow-key nudging (0.001 / 0.01), polyline vertex
  insert/delete, and a JSON panel with copy / download / apply / revert. The
  real overlay redraws live as you drag.
- `app.js` exposes a small `window.PKTR_EDIT` hook (layout, viewBox, rebuild);
  `index.html` loads `edit.js` deferred. `docs/overlay-editing.md` documents
  the coordinate model and the editor.

### Learning design - guidance, not walkthroughs
- `docs/learning-design.md`: the game must not ship a copy-paste path to
  controlling the town in 30 minutes. Four help tiers (orientation / opt-in
  nudge that costs points / hidden easter eggs / instructor answer key) and
  the rule that an easter egg gives a fragment, never a finished command.
- `scoring/flags.py` `hint` strings + `docs/districts/*.md` audited to Tier-1:
  bug class, tool family, the surface to look at, the fix - no working
  payloads, parameters, credentials, or flag locations. Two matching spills in
  `docs/architecture.md` scrubbed.
- The step-by-step for all 20 techniques moved to `instructor/answer-key.md`
  (Tier 4, not something the player's client can pull for free).
- `ROADMAP.md`: Phase 5 split into 5a (Diner Wi-Fi) + 5b (a new idea - a
  default-cred SOHO router in a house; the homeowner is a railroad engineer
  who logs into the rail portal in cleartext, so you sniff the router and
  replay the reused creds into OT). Phase 6 gains the easter-egg hint system.

### Phase 3d - the Packet River IBM z16 (RACF green screen)
- `mainframe/z16/`: a real TN3270E host (RACF logon panel, TSO READY, ISPF,
  SDSF, JCL/SUBMIT), vendored from web3270's `mock-lpar` (GPL-3.0, attribution
  header, node builtins only, ships `jcl/programs/*.jcl`). One addition: a RACF
  command family at the READY prompt - `LISTUSER` / `RLIST` / `SETROPTS LIST` -
  surfacing three curated, genuine review findings.
- `z16` compose service on `127.0.0.1:8991` (container port 3270), `it-net` +
  `edge-net`, reads the flag from `/run/secret/z16_racf/flag.txt`.
- The exploit: `IBMUSER`/`SYS1` (install default, never revoked - `LISTUSER`
  shows it still holds `SPECIAL OPERATIONS AUDITOR`) logs on; the
  `BANK.XFER.APPROVE` FACILITY profile is `UACC(READ)` and in `WARNING` mode
  (access failures logged but allowed); the reconciliation key sits in that
  profile's world-readable `INSTALLATION DATA`. `SETROPTS LIST` shows
  `NOPROTECTALL` for texture.
- `scoring/flags.py`: `z16_racf` technique (subsystem `bank`, effect
  `bank_drain`, base 275, `loud`). Submitting it drains the bank on the map -
  same effect as the web JWT-`none` path; WARNING-mode approval = fraudulent
  transfers sail through.
- `player`: `scripts/z16_3270.py`, a purpose-built TN3270E client (no arm64
  `x3270`) - drives the host-side TN3270E negotiation, logs on, runs one READY
  command, scrapes the flag off the panel (CP037; decodes the record and
  regexes rather than parsing the 3270 order stream). `pktr-connect` gains it
  as options 3 (RACF pull) and 4 (free-form READY command); the menu is now
  grouped AS/400 / z16 / shell. `targets.py` allowlist += `z16`.
- `overlay.json`: the Bank hotspot gains `terminal: 7681` - clicking it opens
  the z16 terminal alongside the online-banking front door.
- `docs/districts/mainframe.md`: promoted to cover both mainframes; z16
  section added (surfaces, the three RACF findings, TN3270E wire notes,
  hardening, real-world parallels).
- Verified end to end from the player box: log on -> `RLIST` -> flag -> submit
  -> `accepted`, 619 pts (275 x 1.5 speed x 1.5 stealth), the bank reads
  `carded` / balance 0 / alarm cut on the map, alert level ticks to 1.

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
