# District: First Packet Bank & Trust  (`bank_jwt_none`, `bank_account_idor`) — Phase 3

Online banking for the town: a login portal, a customer dashboard, a JSON
accounts API, and a staff-only transfer form. Container: `bank` (Express, its
own in-memory ledger). The bank's alarm panel is wired to the power grid, so
draining the bank also drops the alarm on the map. The z16 core-banking green
screen behind it is a third way into the same damage, written up in
[`mainframe.md`](mainframe.md).

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

## `bank_jwt_none` — the token check honours `alg:none`

| | |
|---|---|
| Surfaces | login portal + dashboard at `http://127.0.0.1:8100/` · session is a JWT in the `bank_jwt` cookie. From the map: click **First Packet Bank & Trust**. |
| The bug | the token verifier accepts a header of `{"alg":"none"}` with no signature. Re-issue your own customer token with an elevated role and the staff dashboard opens; it prints the Fed wire settlement token in the clear. |
| Tool | `curl` + a base64url one-liner, or any JWT tool. |
| Physical result | submitting the flag fires `bank_drain`: `site_status` → `carded`, balance 0, ATM drained, `admin_pwned`, and the grid-tied alarm is cut on the map. Same end state as the z16 RACF path. |
| Flag | shown on the staff/admin dashboard as the "Fed wire settlement token". Read at boot from `/run/secret/bank_jwt_none/flag.txt`. |
| Points | base 200, severity `loud`. |
| Reset | reset panel `bank` scope. A fresh flag is minted on a full `scoring` re-run. |
| Hardened build | pin the accepted algorithm (`HS256` only), reject `none`, and verify the signature against a real key. Never render a settlement token into an HTML page. |
| Real-world | `alg:none` is CVE-2015-9235 and a decade of copies since; it is still found in the wild wherever a library's "verify" path trusts the header's own algorithm claim. MITRE: T1550.001 (application access token). |

## `bank_account_idor` — accounts API with no ownership check

| | |
|---|---|
| Surfaces | `GET /api/accounts/:id` on `http://127.0.0.1:8100/`. |
| The bug | the endpoint returns any account by id with no check that it belongs to the caller. Walk the ids; one account's `memo` field carries a municipal reconciliation token. |
| Tool | `curl` in a loop, or `ffuf`. |
| Physical result | submitting the flag fires `bank_leak`: `site_status` → `db_dumped` on the map (customer data exposed, no drain). |
| Flag | in the `memo` of the municipal operating account. Read at boot from `/run/secret/bank_account_idor/flag.txt`. |
| Points | base 125, severity `medium`. |
| Reset | reset panel `bank` scope. |
| Hardened build | enforce ownership on every account read (the caller's token subject must match the account holder, or hold a real staff role), and keep secrets out of free-text fields. |
| Real-world | broken object-level authorization is OWASP API Security #1 (API1:2023); IDOR on a numeric account id is the textbook case. MITRE: T1213 (data from information repositories). |
