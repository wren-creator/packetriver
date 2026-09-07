# Packet River verification runbook

End-to-end checks. **Section A is containment, run it first and last every
session.** Section B walks the attack side on the flat topology. Section C is
reset. Section D is the defended re-run. Section E is the ebook.

Attacker commands run inside the `player` box:

```bash
docker compose exec player sh
ls /opt/pktr/scripts
```

Web techniques that don't have a bundled script are driven per
[`../instructor/answer-key.md`](../instructor/answer-key.md); the pass
condition is the same either way, the named map effect lands within ~2 s of a
valid submission and `POST /api/score/submit` returns `{"accepted": true}`.

## Section A — containment (run first and last)

| # | Command | Pass condition |
|---|---|---|
| A1 | `./status.sh` | exits 0; every service healthy; prints the loopback audit with no `[x]` except the known Phase-4 `player → traffic-plc` pivot line |
| A2 | `docker compose ps --format '{{.Name}}\t{{.Ports}}'` | every published mapping reads `127.0.0.1:` |
| A3 | `docker compose exec player sh -c 'cat /etc/resolv.conf'` | resolver is the town DNS (`172.31.20.253` via `ExtServers`), search `packetriver.range` |
| A4 | `docker compose exec player python3 -c 'import socket;print(socket.socket().connect_ex(("1.1.1.1",53)))'` | non-zero (internet unreachable) |
| A5 | `docker compose exec player sh -c 'command -v sqlmap nmap dig mosquitto_pub'` | all four resolve |
| A6 | from another machine on your LAN: `nmap -Pn -p 8080,8090,8091,8092,8093,8100,8500,1883,2323 <this-host-ip>` | all filtered / closed (nothing bound off loopback) |

## Section B — per-technique (attack side, `./start.sh`)

Register and start a run once (`/api/score/register`, `/api/score/run`), then
`arm` each technique before you work it so the stealth / speed bonus is scored.

### Group A — Main Street

| # | Steps | Pass condition |
|---|---|---|
| B1 `generalstore_sqli` | `sqlmap` the product search (answer key) | schema + the flag row extracted; submit → General Store ring flips to `db_dumped` on the map |
| B2 `hardware_idor` | walk the order id with `curl`/`ffuf` (answer key) | another order's flag field returned; submit → Hardware `db_dumped` |
| B3 `pharmacy_authbypass` | crafted username in the portal login (answer key) | session granted without a valid password; flag on the landing page; submit → Pharmacy `db_dumped` |
| B4 `diner_backup` | content discovery for the backup file (answer key) | the dump downloads; flag inside; submit → Diner `db_dumped` |
| B5 `barber_xss` | script payload in the booking note (answer key) | the "manager" review fires; flag returned; submit → Barbershop `defaced` |
| B6 `tavern_defaultcreds` | vendor default on the POS admin (answer key) | admin session; flag shown; submit → Tavern `carded` |
| B7 `drycleaner_gitleak` | `git-dumper` then read deleted history (answer key) | secret + flag recovered; submit → Dry Cleaners `db_dumped` |
| B8 `baittackle_ssrf` | point the image fetch at the internal target (answer key) | internal response body returned; flag inside; submit → Bait & Tackle `db_dumped` |

### Group B — civic + payments

| # | Steps | Pass condition |
|---|---|---|
| B9 `townhall_deface` | clerk login, post a notice with markup (answer key) | confirm code (flag) returned; the map announcement board shows the text; Town Hall `defaced` |
| B10 `townhall_lfi` | payroll login, traversal in `payslip.php?doc=` (answer key) | the flag file reads out; submit → Town Hall `payroll_balance` 0 and `admin_pwned` |
| B11 `police_leak` | request the exposed config path (answer key) | flag in the JSON; submit → Police `defaced` |
| B12 `fire_defaultcreds` | vendor default on the alarm panel (answer key) | flag shown; submit → Fire `defaced` |
| B13 `paygw_receipt_idor` | `curl` walking `/receipt/<txn>` on `:8500` | seeded receipt memo carries the flag; submit → every healthy shop flips `carded`, `fraud_charges` climb |
| B14 `as400_empmast` | `python3 /opt/pktr/scripts/as400_5250.py` menu option 1 | negotiates 5250, signs on, runs the `SELECT`, scrapes `PKTR{...}`; submit → Town Hall payroll drained |

### Group C — First Packet Bank & Trust

| # | Steps | Pass condition |
|---|---|---|
| B15 `bank_jwt_none` | forge an `alg:none` token with an elevated role (answer key) | staff dashboard renders the "Fed wire settlement token" (flag); submit → bank `carded`, balance 0, ATM drained, alarm cut on the map |
| B16 `bank_account_idor` | `curl` over `/api/accounts/:id` on `:8100` | the municipal account's `memo` carries the flag; submit → bank `db_dumped` |
| B17 `z16_racf` | `python3 /opt/pktr/scripts/z16_3270.py` menu option 3 | negotiates TN3270E, logs on, `RLIST` scrapes `PKTR{...}`; submit → bank drain (same end state as B15) |

### Group D — utilities / OT

| # | Steps | Pass condition |
|---|---|---|
| B18 `water_modbus_pump` | `python3 /opt/pktr/scripts/modbus_attack.py` water pump stop + read the flag block in maint mode | mains pressure falls over a few ticks; houses on the map go dry, a main bursts; submit accepted |
| B19 `power_modbus_feeder` | `modbus_attack.py` trip a feeder + read the flag block | that load goes dark on the map; frequency sags; submit accepted |
| B20 `factory_modbus` | `modbus_attack.py` against `:5504` + read the flag block | Widget Factory trouble ring, throughput drops; submit accepted |
| B21 `sewage_modbus` | `modbus_attack.py` open the bypass (or stop aeration/dose) + read the flag block | effluent path goes raw; river contamination climbs; the plume mosaic spreads from the beach; swimmers sicken (cascade bonus); submit accepted |
| B22 `traffic_mqtt` | `python3 /opt/pktr/scripts/traffic_attack.py all-green` then `flag` | the intersection dot locks green, "hijacked" pulse, crash count climbs; the engineering-mode PIN yields the flag; submit accepted |
| B23 `rail_console` | `python3 /opt/pktr/scripts/rail_attack.py flag`, then `spur` as the train nears the branch | the train routes onto the spur under the "R" of "Main Rail Line", runs it ~5 s, derails into the Widget Factory; fire ring; submit accepted |

### Group E — recon

| # | Steps | Pass condition |
|---|---|---|
| B24 `dns_axfr` | `python3 /opt/pktr/scripts/recon.py dns` | the AXFR returns the whole `packetriver.range` zone including `scada-legacy-07 ... PKTR{...}`; submit → 75 base, no map change |

### Anti-cheat

| # | Steps | Pass condition |
|---|---|---|
| B25 | `curl -X POST` every `simmap` route | no route awards points |
| B26 | submit a random string, and a real flag minted in a different run | both rejected, generic `{"accepted": false}`, Alert heat ticks up |
| B27 | `docker compose exec player sh -c 'ls /run/secret 2>&1'` | not mounted, the player box never sees a flag file |
| B28 | `docker compose exec simmap sh -c 'ls /run/secret 2>&1'` | not mounted |

### Alert Level + blue team

| # | Steps | Pass condition |
|---|---|---|
| B29 | run several `loud` techniques quickly; watch `GET /api/score/me` `alert_level` | climbs through the bands (20/45/75/110/150) with downward hysteresis |
| B30 | cross Level 2 | the field-plc HMI operator logins rotate (`pkt/creds/rotate`); `GET /ops/handover.txt` on `:8093` shows the new set; the traffic PIN and rail console password rotate |
| B31 | cross Level 5 | the worst-hit subsystem auto-restores to golden |

## Section C — reset

| # | Command | Pass condition |
|---|---|---|
| C1 | in-game reset panel, one subsystem scope | that node returns to golden; a fresh flag is armed for its technique(s) |
| C2 | `./reset.sh -y` | completes; all containers healthy; town fully golden; scoreboard run state cleared |
| C3 | `curl -s http://127.0.0.1:8080/api/state` | every subsystem reads its golden value; `rail.on_spur` / `derailed` false; `alert_level` 0 |

## Section D — defended side (`./start.sh --segmented`)

| # | Steps | Pass condition |
|---|---|---|
| D1 | `./start.sh --segmented` | comes up healthy; `docker-compose.segmented.yml` folded in |
| D2 | re-run B18–B21 (Modbus) | `MODBUS_WRITE_OPEN=0`, the PLC re-asserts golden every scan; the flag block stays locked |
| D3 | re-run B22 (`traffic_attack.py`) | the broker `acl.segmented` + `passwd.segmented` refuse the anonymous publish |
| D4 | re-run B23 (`rail_attack.py`) | the console credentials are rotated; default login refused |
| D5 | re-check the web tier | `VERBOSE_ERRORS=0`, `WEAK_SESSIONS=0`; error-based extraction and weak-token paths are blunted |

## Section E — ebook (Phase 6, not built yet)

| # | Command | Pass condition |
|---|---|---|
| E1 | `cd docs/syllabus-epub && ./build-epub.sh` | `mimetype` is the first entry and `stored` (not deflated) |
| E2 | `epubcheck docs/Packet-River-101.epub` (if installed) | no errors |
