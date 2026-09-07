# District: Civic + payments  (`townhall_deface`, `townhall_lfi`, `police_leak`, `fire_defaultcreds`, `paygw_receipt_idor`) — Phase 3

Town Hall (public announcements + payroll), the Police blotter, the Fire
station alarm panel, and the card gateway that every checkout in town posts to.
The web pieces are vhosts on the shared `websites` container; the gateway is
its own `paygw` container. The AS/400 payroll green screen behind Town Hall is
a sixth way to drain the same payroll account, written up in
[`mainframe.md`](mainframe.md).

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

## `townhall_deface` — weak clerk login + stored XSS on the public board

| | |
|---|---|
| Surfaces | `http://127.0.0.1:8090/townhall/` (public board) · `/townhall/admin.php` (clerk login). From the map: click **Town Hall**. |
| The bug | the clerk's office takes a weak default login. Once in, the notice you post is stored raw and rendered raw on the public board (stored XSS / defacement); the "published" confirmation code is the flag. |
| Tool | `curl`, or a browser. |
| Physical result | `cityhall_deface`: the announcement board on the map shows your text and `site_status` → `defaced`. |
| Flag | the confirmation code returned when a notice is published. Read at boot from `/run/secret/townhall_deface/flag.txt`. |
| Points | base 100, severity `loud`. |
| Reset | reset panel `cityhall` scope restores the board. |
| Hardened build | real authentication on the clerk's office, output-encode the notice body, add a CSP. |
| Real-world | stored XSS on a CMS/notice board is one of the most common defacement vectors; MITRE T1189 / T1059.007. |

## `townhall_lfi` — path traversal in the payslip viewer

| | |
|---|---|
| Surfaces | `/townhall/payroll.php` (payroll login) → `/townhall/payslip.php?doc=...`. |
| The bug | `doc` is concatenated onto the payslips directory with no sanitisation, so `../` walks out to anything the web user can read. |
| Tool | `curl`. |
| Physical result | `cityhall_payroll`: Town Hall's `payroll_balance` → 0 and `admin_pwned` on the map. Same end state as the AS/400 path. |
| Flag | a file under `/run/secret/townhall_lfi/`, reachable by traversing to it. |
| Points | base 175, severity `loud`. |
| Reset | reset panel `cityhall` scope. |
| Hardened build | canonicalise the resolved path and confine it under the payslips base directory; reject any `doc` containing a separator or `..`. |
| Real-world | LFI / path traversal is CWE-22, OWASP A01; MITRE T1083 / T1005. |

## `police_leak` — dispatch config left in the web root

| | |
|---|---|
| Surfaces | the Police blotter at `/police/`. The bug is not in the app: `/police/dispatch/config.json` is world-readable. |
| Tool | content discovery (`ffuf`), or just request the path. |
| Physical result | `police_deface`: `site_status` → `defaced` on the map. |
| Flag | a value in the exposed config file. Read at boot from `/run/secret/police_leak/flag.txt`. |
| Points | base 75, severity `quiet`. |
| Reset | reset panel `police` scope. |
| Hardened build | keep operational config out of the docroot; block dotfiles and `*.json` config paths at the server. |
| Real-world | secrets in a web-served config file is CWE-538 / OWASP A05 (security misconfiguration). |

## `fire_defaultcreds` — station alarm panel default login

| | |
|---|---|
| Surfaces | the Fire station alarm panel at `/fire/`. |
| The bug | the panel takes a shared default credential. |
| Tool | try the vendor default, or `hydra` a short list. |
| Physical result | `fire_deface`: `site_status` → `defaced` on the map. |
| Flag | shown once signed in. Read at boot from `/run/secret/fire_defaultcreds/flag.txt`. |
| Points | base 75, severity `medium`. |
| Reset | reset panel `fire` scope. |
| Hardened build | force a credential change at install; never ship shared defaults. |
| Real-world | default credentials on alarm / building-management panels is a standing pen-test finding; CWE-1392, MITRE T1078.001. |

## `paygw_receipt_idor` — card gateway receipt endpoint

| | |
|---|---|
| Surfaces | `GET /receipt/<txn>` on `http://127.0.0.1:8500/` (no auth, sequential ids). |
| The bug | any receipt is readable by id with no auth and no ownership check. One seeded receipt's memo carries the flag. |
| Tool | `curl` in a loop. |
| Physical result | `paygw_carded`: fraud spreads, every healthy shop's `site_status` → `carded` and `fraud_charges` climb across Main Street. |
| Flag | in a seeded receipt's memo. Read at boot from `/run/secret/paygw_receipt_idor/flag.txt`. |
| Points | base 150, severity `loud`. |
| Reset | reset each affected storefront's own scope (`generalstore`, `hardware`, ...), or `all`. |
| Hardened build | authorise every receipt read against the caller; don't use guessable sequential ids for the public handle. |
| Real-world | IDOR on payment receipts / invoices leaks PANs and PII at scale; OWASP API1:2023, PCI-DSS 7. The card data here is vendor **test** PANs only, non-functional (see the header comment in `paygw/cards.py`). |
