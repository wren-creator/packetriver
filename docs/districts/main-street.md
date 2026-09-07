# District: Main Street

Eight storefronts, one bug class each, so no two teach the same thing. Each is a
vhost in the `websites` container (PHP 8 + Apache) behind a login portal styled
after the Cross Creek HMI logons and Widgetorium's `login.php`. Town Hall,
Police, Fire, and payments are in [`civic.md`](civic.md); the bank is in
[`bank.md`](bank.md); the cinema and bakery are set dressing.

These pages give **direction, not a walkthrough** (see
[`../learning-design.md`](../learning-design.md)). The step-by-step for every
technique is in [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

## General Store  (`generalstore_sqli`) — shipped in Phase 1

| | |
|---|---|
| Surface | `http://127.0.0.1:8090/` — a login portal, then a catalogue with a product search. |
| Front door | the portal login. A seeded customer account exists, and registration is safe (parameterised). The portal is not the bug. |
| The bug | error-based SQL injection in the product search: user input is concatenated into the query, and DB errors are shown on the page. The search term is also reflected without encoding. |
| Tool | `sqlmap`, or a hand-built `UNION`. |
| Map effect | `shop[generalstore].site_status = "db_dumped"` — orange status ring + a "db dumped" badge over the store. Alert Level +1 (severity `medium`). |
| Points | base 150, times the stealth / chain / speed multipliers. |
| Real-world | classic error-based SQLi via string concatenation. OWASP A03:2021 Injection. Fix: a bound parameter for the search term, and output-encoding on the reflected value. |

## The other seven — Phase 3a-1 (shipped)

Structure: one `websites` docroot, one subdirectory per shop
(`http://127.0.0.1:8090/<key>/`), each its own MariaDB schema. Shared login
portal in `site/lib/portal.php`; a seeded customer account exists on each.

| Shop | `technique_id` | Bug class | Tool |
|---|---|---|---|
| Hardware & Supply | `hardware_idor` | IDOR on an order/receipt lookup — the record id is trusted, never checked against your session | `curl` / `ffuf` |
| Riverside Pharmacy | `pharmacy_authbypass` | authentication bypass in the portal login — the query is string-built, so input becomes logic | `sqlmap` / manual |
| The Daily Grind (Diner) | `diner_backup` | a database backup left somewhere under the web root | content discovery (`ffuf`) |
| Two Chairs Barbershop | `barber_xss` | stored XSS in the booking form; an automated "manager" review opens each new booking (a regex bot on a loop, **not** a real browser) and your script runs in its context | browser / `curl` |
| The Watering Hole (Tavern) | `tavern_defaultcreds` | default credentials on the POS / jukebox admin | `hydra` |
| Packet River Cleaners | `drycleaner_gitleak` | a version-control directory exposed under the web root; deleted history is recoverable | `git-dumper`, then `git log -p` |
| Bait & Tackle | `baittackle_ssrf` | SSRF in a "fetch product image by URL" feature — it will reach services only the server can | `curl` |

The Diner also opens a separate **network lane** in Phase 5 (open Wi-Fi,
`netlab`) on top of the backup-file bug.

Map effect on a valid submission: `shop[<key>].site_status` -> `db_dumped`
(data-leak bugs), `defaced` (XSS), or `carded` (creds). Alert heat per the
technique's severity; the chain bonus stacks across shops in one run.

Fixes, by bug class: parameterised queries + real auth checks (SQLi,
auth-bypass); enforce record ownership server-side (IDOR); keep backups and
repositories out of the docroot and block dotfiles at the server (backup leak,
`.git` leak); output-encode on render + a CSP (stored XSS); force a credential
change on first use, no shared defaults (default creds); allowlist egress and
block loopback / link-local (SSRF).
