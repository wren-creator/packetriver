# Packet River scenarios, trainee edition

Twenty-four planted weaknesses in five groups. This is the instructor edition
with the **Fix** line removed from each entry: work out the remediation
yourself, then check it against [`scenarios.md`](scenarios.md).

Packet River deliberately does **not** ship a copy-paste path to owning the
town (see [`learning-design.md`](learning-design.md)). Each entry here gives the
mechanism, the real-world parallel, the MITRE mapping, the tool family, the
surface, and the physical consequence, enough to know what you are looking for
and how to confirm it. The exact request, sign-on, or payload is yours to
build. The district docs under [`districts/`](districts/) carry the same
Tier-1 detail, and there is an opt-in in-game hint that costs points.

Every consequence below was observed on the running flat range
(`./start.sh`), driving each technique from the `player` box and submitting the
flag through the map.

Entry shape:

```
### <technique_id> — <short title>
**Where:** <host / port / surface>
**Real-world parallel:** <incident or CVE>
**Vulnerability:** <mechanism>
**MITRE ATT&CK:** <technique IDs>
**Confirm / exploit with:** <tool family + surface; the exact request is yours to build>
**Physical consequence:** <what the map does>
**Points / severity:** <base> / <severity>
**Fix:** _work this out, then check the instructor edition._
```

Get a shell on the attacker box first:

```bash
docker compose exec player sh
ls /opt/pktr/scripts
```

---

## Group A — Main Street storefronts

One bug class per storefront, so no two teach the same thing. All eight are
vhosts on the shared `websites` container, published on `127.0.0.1:8090`,
each behind a login portal.

### generalstore_sqli — error-based SQL injection
**Where:** `generalstore` storefront, the authenticated product search.
**Real-world parallel:** the LIKE-clause concatenation bug is the shape behind countless breaches; CWE-89, and error-based extraction is straight out of sqlmap's own test suite.
**Vulnerability:** the search term is concatenated into a `LIKE` clause; verbose DB errors are on, so the database walks you through its own schema.
**MITRE ATT&CK:** T1190 (exploit public-facing application), T1213 (data from information repositories).
**Confirm / exploit with:** `sqlmap` against the search parameter, or a hand-built `UNION`. Find the parameter and the flag yourself.
**Physical consequence:** `shop_sqli_dump`, the General Store reads `db_dumped` on the map.
**Points / severity:** 150 / medium.
**Fix:** _work this out, then check the instructor edition._

### hardware_idor — IDOR on an order/receipt lookup
**Where:** `hardware` storefront, the order/receipt view.
**Real-world parallel:** broken object-level authorization, OWASP API1:2023; the Panera Bread and USPS "Informed Visibility" leaks are the canonical mass-IDOR cases.
**Vulnerability:** the record id is trusted and never checked against the caller's session, so incrementing it walks every order.
**MITRE ATT&CK:** T1190, T1213.
**Confirm / exploit with:** `curl` / `ffuf` walking the id. Walk it yourself.
**Physical consequence:** `shop_sqli_dump`, Hardware reads `db_dumped`.
**Points / severity:** 100 / quiet.
**Fix:** _work this out, then check the instructor edition._

### pharmacy_authbypass — authentication bypass in the portal login
**Where:** `pharmacy` storefront, the portal login.
**Real-world parallel:** `' OR '1'='1` auth bypass, CWE-89 / CWE-287; still found in embedded admin panels every year.
**Vulnerability:** the login query is string-built, so input becomes logic and the password check collapses.
**MITRE ATT&CK:** T1190, T1078 (valid accounts).
**Confirm / exploit with:** a crafted username in the login form; `sqlmap` will also find it.
**Physical consequence:** `shop_sqli_dump`, Pharmacy reads `db_dumped` (records leaked).
**Points / severity:** 125 / medium.
**Fix:** _work this out, then check the instructor edition._

### diner_backup — a database backup left under the web root
**Where:** `diner` storefront; a backup file served from the docroot.
**Real-world parallel:** exposed `.sql` / `.zip` backups are a perennial content-discovery win; CWE-538.
**Vulnerability:** a database dump is reachable by URL because it was written somewhere the web server serves.
**MITRE ATT&CK:** T1083 (file and directory discovery), T1530 (data from web-served storage).
**Confirm / exploit with:** content discovery (`ffuf`), or read what the pages hint at.
**Physical consequence:** `shop_sqli_dump`, the Diner reads `db_dumped`.
**Points / severity:** 100 / quiet.
**Fix:** _work this out, then check the instructor edition._

### barber_xss — stored XSS picked up by a review bot
**Where:** `barber` storefront, the booking form.
**Real-world parallel:** stored XSS against a back-office reviewer; MySpace's Samy worm is the archetype.
**Vulnerability:** the booking note is stored raw and rendered raw in an automated "manager" review, so your script runs in their context. The bot is a regex, never a real browser.
**MITRE ATT&CK:** T1059.007 (JavaScript), T1189 (drive-by compromise).
**Confirm / exploit with:** a script payload in the booking note.
**Physical consequence:** `shop_xss_deface`, the Barbershop reads `defaced`.
**Points / severity:** 100 / medium.
**Fix:** _work this out, then check the instructor edition._

### tavern_defaultcreds — default credentials on the POS/jukebox admin
**Where:** `tavern` storefront, the POS / jukebox admin login.
**Real-world parallel:** default creds on point-of-sale and kiosk admin panels; CWE-1392, Mirai's whole business model.
**Vulnerability:** the admin panel still has its vendor default login, and the session token is weak.
**MITRE ATT&CK:** T1078.001 (default accounts), T1110 (brute force).
**Confirm / exploit with:** the vendor default, or `hydra` a short list.
**Physical consequence:** `shop_carded`, the Tavern reads `carded`.
**Points / severity:** 125 / medium.
**Fix:** _work this out, then check the instructor edition._

### drycleaner_gitleak — exposed `.git` directory
**Where:** `drycleaner` storefront; `.git/` served under the docroot.
**Real-world parallel:** exposed `.git` is a standing bug-bounty find; CWE-527.
**Vulnerability:** the deployed tree includes its version-control directory, so the repo (including deleted history with a secret) can be reconstructed.
**MITRE ATT&CK:** T1083, T1552.001 (credentials in files).
**Confirm / exploit with:** `git-dumper`, then read the history.
**Physical consequence:** `shop_sqli_dump`, the Dry Cleaners reads `db_dumped`.
**Points / severity:** 100 / quiet.
**Fix:** _work this out, then check the instructor edition._

### baittackle_ssrf — SSRF in "fetch product image by URL"
**Where:** `baittackle` storefront, the image-fetch feature.
**Real-world parallel:** Capital One, 2019, SSRF to the cloud metadata endpoint. CWE-918.
**Vulnerability:** the server fetches an attacker-supplied URL with no egress control, so it can be pointed at something only the server can reach.
**MITRE ATT&CK:** T1190, T1135 (network share discovery) / T1046 (network service discovery) via the pivot.
**Confirm / exploit with:** `curl` driving the fetch parameter at an internal target.
**Physical consequence:** `shop_sqli_dump`, Bait & Tackle reads `db_dumped`.
**Points / severity:** 150 / medium.
**Fix:** _work this out, then check the instructor edition._

---

## Group B — Civic + payments

Town Hall, Police, Fire (vhosts on `websites`), the `paygw` card gateway, and
the AS/400 payroll green screen. Full writeups in
[`districts/civic.md`](districts/civic.md) and
[`districts/mainframe.md`](districts/mainframe.md).

### townhall_deface — weak clerk login + stored XSS on the public board
**Where:** Town Hall clerk's office → the public announcement board.
**Real-world parallel:** CMS defacement via a weak admin and an unencoded notice field; MITRE T1491.001 (internal defacement).
**Vulnerability:** weak default clerk login; the posted notice is stored raw and rendered raw on the public board.
**MITRE ATT&CK:** T1078, T1059.007, T1491.
**Confirm / exploit with:** the clerk login, then a notice with markup.
**Physical consequence:** `cityhall_deface`, the map's announcement board shows your text; Town Hall reads `defaced`.
**Points / severity:** 100 / loud.
**Fix:** _work this out, then check the instructor edition._

### townhall_lfi — path traversal in the payslip viewer
**Where:** Town Hall payroll login → the payslip document viewer.
**Real-world parallel:** LFI / path traversal, CWE-22, OWASP A01; the shape behind many "read /etc/passwd, then read the app secret" chains.
**Vulnerability:** the `doc` parameter is concatenated onto a path with no sanitisation, so `../` escapes the payslips directory.
**MITRE ATT&CK:** T1190, T1083, T1005 (data from local system).
**Confirm / exploit with:** `curl` with a traversal in the `doc` parameter.
**Physical consequence:** `cityhall_payroll`, Town Hall `payroll_balance` → 0, `admin_pwned`. Same end state as the AS/400 path.
**Points / severity:** 175 / loud.
**Fix:** _work this out, then check the instructor edition._

### police_leak — dispatch config left in the web root
**Where:** the Police blotter; a config file reachable by URL.
**Real-world parallel:** secrets in a web-served config file, CWE-538 / OWASP A05.
**Vulnerability:** the dispatch team's config sits where the web server serves it.
**MITRE ATT&CK:** T1083, T1552.001.
**Confirm / exploit with:** content discovery, or request the known path.
**Physical consequence:** `police_deface`, the Police Station reads `defaced`.
**Points / severity:** 75 / quiet.
**Fix:** _work this out, then check the instructor edition._

### fire_defaultcreds — station alarm panel default login
**Where:** the Fire station alarm panel login.
**Real-world parallel:** default creds on building-management / alarm panels; CWE-1392.
**Vulnerability:** the panel takes a shared default credential.
**MITRE ATT&CK:** T1078.001.
**Confirm / exploit with:** the vendor default, or `hydra`.
**Physical consequence:** `fire_deface`, the Fire Department reads `defaced`.
**Points / severity:** 75 / medium.
**Fix:** _work this out, then check the instructor edition._

### paygw_receipt_idor — card gateway receipt endpoint
**Where:** `paygw` on `127.0.0.1:8500`, `GET /receipt/<txn>` (no auth, sequential ids).
**Real-world parallel:** IDOR on invoices/receipts leaking PANs and PII; OWASP API1:2023, PCI-DSS 7.
**Vulnerability:** any receipt is readable by id, no auth, no ownership check.
**MITRE ATT&CK:** T1190, T1213.
**Confirm / exploit with:** `curl` walking `<txn>`.
**Physical consequence:** `paygw_carded`, fraud spreads: every healthy shop → `carded`, `fraud_charges` climb across Main Street.
**Points / severity:** 150 / loud.
**Fix:** _work this out, then check the instructor edition._

### as400_empmast — AS/400 payroll green screen (Phase 3c)
**Where:** TN5250 on `127.0.0.1:8992` behind Town Hall.
**Real-world parallel:** blank / default IBM i credentials and `*PUBLIC *ALL` on application libraries are standing AS/400 review findings.
**Vulnerability:** three stacked, all real, a blank password is accepted for any profile; a powerful profile keeps its shipped default password; the payroll library is readable to the public, so Interactive SQL walks right in.
**MITRE ATT&CK:** T1078.001, T1190, T1213; cleartext TN5250 → T1040 (network sniffing).
**Confirm / exploit with:** `as400_5250.py` on the player box (menu option 1), or hand-drive from the `ttyd` terminal.
**Physical consequence:** `cityhall_payroll`, Town Hall `payroll_balance` → 0, `admin_pwned`.
**Points / severity:** 200 / loud.
**Fix:** _work this out, then check the instructor edition._

---

## Group C — First Packet Bank & Trust

Online banking (`bank`, Express, `127.0.0.1:8100`) and the z16 core-banking
green screen behind it. Full writeups in
[`districts/bank.md`](districts/bank.md) and
[`districts/mainframe.md`](districts/mainframe.md).

### bank_jwt_none — the token check honours `alg:none`
**Where:** `bank` session JWT in the `bank_jwt` cookie; the staff dashboard.
**Real-world parallel:** CVE-2015-9235 and a decade of copies.
**Vulnerability:** the verifier accepts `{"alg":"none"}` with no signature. Forge an elevated role and the staff dashboard opens, printing the Fed wire settlement token in the clear.
**MITRE ATT&CK:** T1550.001 (application access token), T1190.
**Confirm / exploit with:** `curl` + a base64url one-liner, or any JWT tool.
**Physical consequence:** `bank_drain`, `carded`, balance 0, ATM drained, `admin_pwned`, grid-tied alarm cut on the map.
**Points / severity:** 200 / loud.
**Fix:** _work this out, then check the instructor edition._

### bank_account_idor — accounts API with no ownership check
**Where:** `GET /api/accounts/:id` on `127.0.0.1:8100`.
**Real-world parallel:** OWASP API1:2023; IDOR on a numeric account id.
**Vulnerability:** any account is returned by id with no ownership check. One account's `memo` carries a municipal reconciliation token.
**MITRE ATT&CK:** T1190, T1213.
**Confirm / exploit with:** `curl` in a loop over the ids.
**Physical consequence:** `bank_leak`, the bank reads `db_dumped` (data exposed, no drain).
**Points / severity:** 125 / medium.
**Fix:** _work this out, then check the instructor edition._

### z16_racf — RACF WARNING mode + world-readable profile (Phase 3d)
**Where:** TN3270E on `127.0.0.1:8991` behind the Bank.
**Real-world parallel:** a never-revoked default admin with its shipped password, and profiles left in WARNING mode for years, are standing z/OS audit hits.
**Vulnerability:** three real findings, a default admin still holds `SPECIAL` + `OPERATIONS` and still logs on; a transfer-approval profile is world-readable and in `WARNING` mode (fail-open); globally `NOPROTECTALL`. A reconciliation key sits in that profile's readable metadata.
**MITRE ATT&CK:** T1078.001, T1222 (permission modification weakness), T1552; cleartext TN3270 → T1040.
**Confirm / exploit with:** `z16_3270.py` on the player box (menu option 3), or hand-drive RACF from the `ttyd` terminal.
**Physical consequence:** `bank_drain`, same end state as the JWT path.
**Points / severity:** 275 / loud.
**Fix:** _work this out, then check the instructor edition._

---

## Group D — Utilities / OT

Water, power, the widget-factory line, and sewage are real Modbus/TCP soft-PLCs
in the `field-plc` container. Traffic is commanded over the open MQTT bus;
rail is a raw-TCP console. Full writeups in
[`districts/water.md`](districts/water.md),
[`power.md`](districts/power.md), [`sewage.md`](districts/sewage.md),
[`traffic.md`](districts/traffic.md), [`rail.md`](districts/rail.md).

### water_modbus_pump — unauthenticated Modbus write
**Where:** `field-plc` water PLC, Modbus/TCP `127.0.0.1:5502` (container `502`).
**Real-world parallel:** Oldsmar FL 2021 (setpoint change was the attack); FrostyGoop, Lviv 2024 (plain Modbus knocked out heat to ~600 buildings).
**Vulnerability:** Modbus/TCP has no auth, no session, no integrity. Any host that can open 502 reads and writes every coil and register. The flag block unlocks while the PLC is in maintenance mode.
**MITRE ATT&CK for ICS:** T0855 (unauthorized command message), T0831 (manipulation of control), T0836 (modify parameter), T0813 (denial of control).
**Confirm / exploit with:** `pymodbus` / `modbus_attack.py`.
**Physical consequence:** stop the high-lift pump and mains pressure bleeds out over a few ticks; houses on the map go dry, then a main bursts.
**Points / severity:** 175 / loud.
**Fix:** _work this out, then check the instructor edition._

### power_modbus_feeder — unauthenticated Modbus write
**Where:** `field-plc` power PLC, Modbus/TCP `127.0.0.1:5503` (container `503`).
**Real-world parallel:** Ukraine 2015/2016 grid attacks (operator HMIs and breaker control abused).
**Vulnerability:** as above, open Modbus on the substation bus; breakers are just coils and nothing checks the writer.
**MITRE ATT&CK for ICS:** T0855, T0831, T0832 (manipulation of view), T0813.
**Confirm / exploit with:** `pymodbus` / `modbus_attack.py`.
**Physical consequence:** trip a feeder and that load goes dark on the map (houses, streetlights, downtown, or the factory); grid frequency sags.
**Points / severity:** 175 / loud.
**Fix:** _work this out, then check the instructor edition._

### factory_modbus — unauthenticated Modbus write to the assembly line
**Where:** `field-plc` widget-factory PLC, Modbus/TCP `127.0.0.1:5504` (container `504`).
**Real-world parallel:** unsafe writes past a safety interlock; the shape behind many ICS "safety instrumented system" concerns (TRITON/TRISIS, 2017).
**Vulnerability:** the line's safety interlocks are just coils; nothing checks the writer. The flag block unlocks in maintenance mode.
**MITRE ATT&CK for ICS:** T0855, T0831, T0889 (modify program), T0880 (loss of safety).
**Confirm / exploit with:** `pymodbus` / `modbus_attack.py`.
**Physical consequence:** line jam / unsafe run, the Widget Factory shows a trouble ring and throughput drops.
**Points / severity:** 175 / loud.
**Fix:** _work this out, then check the instructor edition._

### sewage_modbus — unauthenticated Modbus write to the sewage PLC
**Where:** `field-plc` sewage PLC, Modbus/TCP `127.0.0.1:5505` (container `505`).
**Real-world parallel:** Maroochy Shire, Queensland 2000, an insider released ~800,000 L of sewage via radio commands to pumping stations.
**Vulnerability:** open Modbus; open the storm bypass, or stop aeration and dosing, and the effluent runs raw.
**MITRE ATT&CK for ICS:** T0855, T0831, T0836, T0828 (loss of productivity/revenue), T0813.
**Confirm / exploit with:** `pymodbus` / `modbus_attack.py`.
**Physical consequence:** the effluent path goes raw; river contamination integrates up and the plume mosaic spreads from the beach; swimmers sicken (cascade bonus).
**Points / severity:** 175 / loud.
**Fix:** _work this out, then check the instructor edition._

### traffic_mqtt — open MQTT command topic
**Where:** the `bus` broker on `127.0.0.1:1883`; the signal controllers' command topic and an engineering-mode topic.
**Real-world parallel:** unauthenticated MQTT brokers are a standing Shodan finding; the 2014 University of Michigan traffic-signal study and Cesar Cerrudo's Sensys Networks work.
**Vulnerability:** on the flat broker the controllers' command topic has no ACL and no auth. A publish locks a crossroads ALL-GREEN. The engineering-mode topic takes a short PIN and, on a match, publishes the flag (non-retained).
**MITRE ATT&CK for ICS:** T0855, T0831, T0814 (denial of service); Enterprise T1090 (proxy) n/a.
**Confirm / exploit with:** `mosquitto_pub` / `mosquitto_sub`, or `traffic_attack.py`.
**Physical consequence:** the intersection's signal dot locks green, the crossroads pulses "hijacked", crashes climb a few seconds later, downtown gridlocks.
**Points / severity:** 175 / loud.
**Fix:** _work this out, then check the instructor edition._

### rail_console — raw-TCP maintenance console + command injection
**Where:** `rail-plc` raw-TCP console on `127.0.0.1:2323`.
**Real-world parallel:** Lodz tram, 2008 ("someone threw the switches"); the long tail of telnet management ports on transit signalling.
**Vulnerability:** two stacked, the console has default credentials, and `set label` hands your input straight to a shell (command injection, CWE-78). Either one reads the maintenance key; `set switch spur` throws the switch.
**MITRE ATT&CK for ICS:** T0812 (default credentials), T0807 (command-line interface), T0855, T0831; Enterprise T1059.
**Confirm / exploit with:** `nc` / `telnet`, or `rail_attack.py`.
**Physical consequence:** set the switch to `spur` before the train reaches the branch (under the "R" of "Main Rail Line") and the train routes onto the spur, runs it to the Widget Factory over ~5 s, and derails into it, factory fire.
**Points / severity:** 200 / loud.
**Fix:** _work this out, then check the instructor edition._

---

## Group E — Recon

### dns_axfr — open DNS zone transfer
**Where:** the `dns` container (CoreDNS) at `172.31.20.253:53`, the `player` box's resolver.
**Real-world parallel:** open AXFR against a misconfigured secondary is one of the oldest external-recon wins; stale records for "retired" kit routinely outlive it.
**Vulnerability:** the `packetriver.range` zone answers AXFR from anyone. One transfer enumerates every host in town, plus a TXT record for a box that was supposed to be decommissioned, with a maintenance token in it.
**MITRE ATT&CK:** T1590.002 (gather victim network information: DNS), T1596.001 (search open technical databases: DNS/passive DNS).
**Confirm / exploit with:** `recon.py dns`, or `dig axfr packetriver.range @dns`.
**Physical consequence:** none, pure recon (`effect: noop`).
**Points / severity:** 75 / quiet.
**Fix:** _work this out, then check the instructor edition._
