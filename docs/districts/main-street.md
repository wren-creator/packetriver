# District: Main Street

Eight storefronts, one bug class each, so no two teach the same thing. Each is a
vhost in the `websites` container (PHP 8 + Apache) behind a login portal styled
after the Cross Creek HMI logons and Widgetorium's `login.php`. The bank, Town
Hall, Police, and Fire are their own writeups; the cinema and bakery are set
dressing.

## General Store  (`generalstore_sqli`) — shipped in Phase 1

| | |
|---|---|
| Surface | `http://127.0.0.1:8090/` — login portal, then a catalogue + a product search |
| Front door | portal login. Seeded account `shopper` / `shopper`, or register (parameterised, safe). The portal itself is not the bug. |
| The bug | `search.php`: the `q` parameter is concatenated straight into `... WHERE name LIKE '%$q%' ORDER BY name`. Three columns are selected (`id, name, price`) so a `UNION SELECT` lines up cleanly. A broken quote drops the failing SQL into the page (verbose errors). The term is echoed back unencoded (reflected XSS). |
| Tool | `sqlmap -u "http://websites/search.php?q=x" --load-cookies=<jar> --batch --dump -T staff_notes -D generalstore`, or by hand: `q=x%' UNION SELECT 1,note,1 FROM staff_notes-- -` |
| Flag location | one row of `staff_notes`. The table has no page; the only way to read it is a UNION out of the search. Planted by the `websites` entrypoint at boot from `/run/secret/generalstore/flag.txt`. |
| Map effect | `shop[generalstore].site_status = "db_dumped"` — orange status ring + a "db dumped" badge over the store. Alert Level +1 (severity `medium`). |
| Points | base 150, times the stealth / chain / speed multipliers. |
| Real-world | classic error-based SQLi via string concatenation. OWASP A03:2021 Injection. The fix: a bound parameter for the `LIKE` term, and output encoding on the reflected value. |

## The other seven — Phase 3a-1 (shipped)

Structure: one `websites` docroot, one subdirectory per shop
(`http://127.0.0.1:8090/<key>/`), each its own MariaDB schema. Shared login
portal in `site/lib/portal.php`; seeded customer `shopper` / `shopper`.

| Shop | `technique_id` | Bug | Tool | Flag |
|---|---|---|---|---|
| Hardware & Supply | `hardware_idor` | `receipt.php?id=` has no ownership check; receipts start at 1001 | `curl` / `ffuf` walk | in one receipt's `notes` |
| Riverside Pharmacy | `pharmacy_authbypass` | the portal login builds its query by concatenation: `username = ' OR role='staff' LIMIT 1 -- -` | `sqlmap` / manual | on `records.php` once you're staff |
| The Daily Grind (Diner) | `diner_backup` | `db_backup.sql` left in the web root | `curl` | a comment in the `.sql` |
| Two Chairs Barbershop | `barber_xss` | stored XSS in the appointment note; a regex "manager bot" (`review.php`, hit on a loop by the container, **not** a real browser) writes its flag onto your booking when the script fires | browser / `curl` | `booking.php?id=<yours>` after the bot runs |
| The Watering Hole (Tavern) | `tavern_defaultcreds` | POS / jukebox admin ships as `admin` / `admin` | `hydra` | the back-office panel |
| Packet River Cleaners | `drycleaner_gitleak` | a browsable `.git` in the web root | `git-dumper` then `git log -p` | `RECOVERY_KEY` in `config.php`'s history |
| Bait & Tackle | `baittackle_ssrf` | `fetch.php?url=` is an open SSRF | `curl` | the localhost-only `/baittackle/_internal/inv.php` |

The Diner also opens a separate **network lane** in Phase 5 (open Wi-Fi,
`netlab`) on top of the backup-file bug.

Map effect on a valid submission: `shop[<key>].site_status` -> `db_dumped`
(data-leak bugs), `defaced` (XSS), or `carded` (creds). Alert heat per the
technique's severity; the chain bonus stacks across shops in one run.

Still open in Phase 3a: `paygw` + a real card checkout on the shops, Town Hall
(payroll + LFI), the Bank district (JWT `none` + ATM + grid-tied alarm),
Police + Fire as minor targets.
