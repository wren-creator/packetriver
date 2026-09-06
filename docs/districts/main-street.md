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

## The other seven — Phase 3

| Shop | Bug | Tool |
|---|---|---|
| Hardware & Supply | IDOR on receipt/order id, no ownership check | `curl` / `ffuf` |
| Pharmacy / Apothecary | auth-bypass + IDOR on prescription/PII records | `sqlmap` / `curl` |
| Local Diner / Café | **network lane** — open unencrypted Wi-Fi, sniff / MITM cleartext creds (Phase 5, `netlab`) | `tcpdump` |
| Barbershop / Salon | stored XSS in the booking form (an "admin bot" regex picks it up) | manual |
| Tavern / Watering Hole | default creds on the POS/jukebox admin + weak session token | `hydra` |
| Dry Cleaners / Laundromat | exposed `.git` with a secret in history + path traversal on the ticket lookup | `git-dumper` |
| Bait & Tackle / Beach Outfitter | SSRF in "fetch product image by URL" | `curl` |
