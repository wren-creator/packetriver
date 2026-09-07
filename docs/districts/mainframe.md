# District: The mainframe tier — Phase 3c / 3d

Two green-screen hosts sit behind the civic web front doors: an **AS/400 (IBM i)**
behind Town Hall for payroll (`as400_empmast`, Phase 3c), and an **IBM z16
(z/OS)** behind First Packet Bank & Trust for core banking (`z16_racf`, Phase
3d). Both are real terminal hosts vendored from
[web3270](https://github.com/wren-creator/web3270) (GPL-3.0); both carry a
handful of curated, genuine bugs rather than a deep OS emulation.

These pages give **direction, not a walkthrough** (see
[`../learning-design.md`](../learning-design.md)). The step-by-step — exact
sign-on, the SQL statement, the RACF command, the flag's field — is in
[`../../instructor/answer-key.md`](../../instructor/answer-key.md).

### Connecting your own terminal

The map's **green screen ↗** link opens a `ttyd` terminal on the player box,
and `as400_5250.py` / `z16_3270.py` drive the scored path headless. For a full
interactive session you can also point any TN5250 / TN3270 client at the
published ports — both containers *are* web3270's own mocks, so its terminal
handles them by construction.

In [web3270](https://github.com/wren-creator/web3270), use the UI's **Manual
Connection** panel ("＋ New session / manual connect…") — no `lpars.txt` edit
needed:

| Host | Host field | Port | Type / model |
|---|---|---|---|
| Packet River AS/400 | `host.docker.internal` | `8992` | AS400 / 5250, model `3179-2` |
| Packet River z16    | `host.docker.internal` | `8991` | TSO / TN3270E, model `3278-2` |

web3270's Bridge runs in its own container, so from inside it `127.0.0.1` is
the bridge, not your host — use `host.docker.internal` (its compose maps that
to the host gateway). `127.0.0.1:8992` / `127.0.0.1:8991` only work from a
client running directly on the host (a bare `node server.js`, `x3270`, `c3270`,
`tn5250` — none of which ship on arm64, hence the purpose-built scripts).

---

## The Packet River AS/400  (`as400_empmast`) — Phase 3c

Behind Town Hall (and, in the story, the Widget Factory) sits an IBM i / AS/400
running payroll on a green screen. It is a real TN5250 host: a SIGNON panel, a
menu tree, DSPMSG, WRKUSRPRF, and Interactive SQL. The mock is vendored from
[web3270](https://github.com/wren-creator/web3270) (GPL-3.0) with one addition —
a small file carrying this session's flag, dropped into the payroll library,
which the box leaves readable to everyone.

| | |
|---|---|
| Surfaces | TN5250 on `127.0.0.1:8992` (container port 3272). From the map: click **Town Hall**, then **green screen ↗** to open the in-browser terminal (`ttyd` on the player box, `:7681`). |
| The bug | Three stacked IBM i misconfigurations, all real: (1) a **weak sign-on** — a blank password is accepted for any profile, the way unhardened low-`QSECURITY` boxes behaved; (2) a **powerful profile still has its shipped default password**; (3) the **payroll library is left readable to the public**, so any signed-on profile can read it from Interactive SQL. |
| Tool | `as400_5250.py` on the player box (menu option 1) drives the whole path: negotiate 5250, sign on, open `STRSQL`, run one `SELECT`, scrape the flag off the result panel. Option 2 lets you run your own `SELECT * FROM lib.table`. Or hand-drive it from the `ttyd` terminal. |
| Physical result | Submitting the flag fires `cityhall_payroll`: Town Hall's `payroll_balance` drops to 0 on the map and `admin_pwned` flips. Same effect the Town Hall web LFI chains into — the payroll money is gone whichever way you got in. |
| Flag | one row in the payroll data, readable once you have a session. Read at mock startup from `/run/secret/as400_empmast/flag.txt`. |
| Points | base 200, severity `loud`. |
| Reset | reset panel `cityhall` scope restores Town Hall's balance and announcement. The AS/400 mints a fresh flag row only on a full `scoring` re-run. |
| Hardened build | On a real box: set `QSECURITY` to 40+, require passwords (no blank sign-on), rotate the shipped default passwords and restrict powerful profiles' device access (`QLMTSECOFR`), and pull `*PUBLIC` down to `*EXCLUDE` on the payroll library with an authorization list for the people who actually run payroll. |
| Real-world | Default and blank IBM i credentials are a standing finding in every AS/400 security review; `*PUBLIC *ALL` on application libraries is the single most common IBM i exposure. TN5250 is cleartext — on a real network this whole exchange, password included, is on the wire. Green-screen depth here is deliberately shallow: a real SIGNON panel and a handful of curated, genuine bugs, not a full OS. |

### Wire notes (for `as400_5250.py`)

The client is small on purpose, in the spirit of `modbus_attack.py`: just enough
5250 to drive the payroll path, not a general-purpose emulator. This documents
how the client talks to the host, not how to exploit it.

- EBCDIC is CP037 (Python's `cp037` codec, both directions).
- Telnet negotiation: server sends `DO NEW-ENVIRON` + `DO TERMINAL-TYPE`; client
  `WILL` both, answers `SB TTYPE IS "IBM-3179-2"` and `SB NEW-ENVIRON IS`
  (empty); server then `DO BINARY` + `DO EOR`, client `WILL` both; the SIGNON
  screen follows once all four are agreed.
- Records: 10-byte GDS header `[len_hi, len_lo, 0x12, 0xA0, 0x00, 0x00, 4, 0, 0,
  0x03]`, then for input `[cursor_row+1, cursor_col+1, AID, SBA(0x11) row+1 col+1
  <cp037 text> ...]`. `0xFF` bytes are doubled; every record is framed with
  `IAC EOR`.
- Field values are matched by row: SIGNON user = row 7, password = row 8; the
  menu command line = row 22; the `STRSQL` statement line = row 5. `AID_ENTER`
  is `0xF1`.
- The client does not parse the WTD order stream — it decodes the whole record
  as CP037 and regexes `PKTR\{...\}` out of the SQL result panel.

For a full interactive green screen, point web3270 at `host.docker.internal:8992`
(see "Connecting your own terminal" above), or hand-drive it from the `ttyd`
link on the map. Vendoring web3270's `tn5250/session.js` into the map panel
itself is still a roadmap follow-up.

---

## The Packet River IBM z16  (`z16_racf`) — Phase 3d

Behind First Packet Bank & Trust runs core banking on a z/OS LPAR: a real
TN3270E host with a RACF logon panel, TSO READY, ISPF, SDSF, JCL/SUBMIT. The
mock is vendored from web3270's `mock-lpar` (GPL-3.0). One addition: a RACF
command family at the READY prompt — `LISTUSER`, `RLIST`, `SETROPTS LIST` —
and a general-resource profile left in a deliberately weak state with this
session's flag parked in its metadata.

| | |
|---|---|
| Surfaces | TN3270E on `127.0.0.1:8991` (container port 3270). From the map: click **First Packet Bank & Trust**, then **z16 green screen ↗** to open the in-browser terminal (`ttyd` on the player box, `:7681`). |
| The bug | Three real, common RACF review findings: (1) a **default admin profile was never revoked** — it still holds `SPECIAL` + `OPERATIONS` and still logs on with its shipped password; (2) a **banking transfer-approval profile is world-readable and in `WARNING` mode** — a failed access check is logged but *allowed*, so the control is fail-open; (3) globally **`NOPROTECTALL`** with WARNING honored. Someone then stashed a reconciliation key in that profile's readable metadata. |
| Tool | `z16_3270.py` on the player box (menu option 3) drives the whole path: negotiate TN3270E, log on, run one `RLIST` at READY, scrape the flag off the panel. Option 4 runs any READY command you type (`LISTUSER`, `SETROPTS LIST`, `LISTAPF`). Or hand-drive it from the `ttyd` terminal. |
| Physical result | Submitting the flag fires `bank_drain`: the bank reads `carded`, balance 0, ATM drained, and the grid-tied alarm drops on the map — the same effect as the web JWT-`none` path. WARNING-mode approval means fraudulent transfers sail through. |
| Flag | in the transfer-approval profile's readable metadata field. Read at mock startup from `/run/secret/z16_racf/flag.txt`. |
| Points | base 275, severity `loud`. |
| Reset | reset panel `bank` scope restores the bank. A fresh flag is minted only on a full `scoring` re-run. |
| Hardened build | Revoke the default admin (or at minimum strip `SPECIAL` / `OPERATIONS` and rotate the password); take the profile out of WARNING mode and set `UACC(NONE)` with an explicit access list; `SETROPTS PROTECTALL(FAILURES)`; and never put secrets in profile metadata — it is readable by anyone who can `RLIST` the profile. |
| Real-world | A never-revoked default admin with its shipped password is a standing pen-test finding on z/OS. WARNING mode is meant to be a migration aid — profiles left in it for years are a classic audit hit (it silently permits every access it would otherwise deny). `NOPROTECTALL` means any dataset with no covering profile is open. TN3270 is cleartext. Green-screen depth here is deliberately shallow: a real RACF logon and a few genuine misconfigurations, not a z/OS emulator. |

### `z16_apf` — a writable APF library

| | |
|---|---|
| The bug | `LISTAPF` lists `USER.LOADLIB` on `WORK01` as APF-authorised, and it is also writable by anyone. `LISTDS 'USER.LOADLIB'` confirms the volume authority. An APF library you can write to is an APF library you can subvert: link an authorised routine in and `CALL` it and you are running in supervisor state, key 0 — total control of the LPAR. |
| Tool | `z16_3270.py "CALL 'USER.LOADLIB(RX01)'"`, or hand-drive at READY. |
| Physical result | fires `bank_drain` (same end state as the RACF and JWT paths). |
| Flag | the escalation token the `CALL` prints. Read at mock startup from `/run/secret/z16_apf/flag.txt`. |
| Points | base 250, severity `loud`. |
| Hardened build | no writable APF libraries; tight authority on the volumes that hold them; program control (`PROGRAM` class) on APF modules; and audit every APF-list change. |
| Real-world | "APF library that is world-writable" is one of the highest-severity findings a z/OS review can produce, and it is not rare. It is a straight line from `UPDATE` on a dataset to key 0. |

### Wire notes (for `z16_3270.py`)

How the client talks TN3270E to the host, not how to exploit it.

- EBCDIC is CP037 (Python's `cp037` codec).
- TN3270E negotiation (host-driven path): host sends `DO TN3270E` / `DO`+`WILL
  BINARY` / `DO`+`WILL EOR`; client `WILL TN3270E`, `WILL`/`DO BINARY`,
  `WILL`/`DO EOR`. Host then `SB TN3270E DEVICE-TYPE REQUEST "IBM-3278-2"` →
  client `SB … DEVICE-TYPE IS "IBM-3278-2"`; host `SB … FUNCTIONS REQUEST` →
  client `SB … FUNCTIONS IS` (empty). The logon panel follows.
- Once TN3270E is up, every record (both directions) carries a 5-byte header
  `[data-type, request-flag, response-flag, seq-hi, seq-lo]`, all zero for
  3270-DATA. Inbound record body: `[AID, cursor-hi, cursor-lo, SBA(0x11) addr
  addr, <cp037 text> …]`. `0xFF` doubled; framed with `IAC EOR`.
- The mock's inbound parser is byte-scanning and forgiving: it skips the 3
  bytes after an SBA and reads the EBCDIC that follows, concatenating all field
  data. So the logon record is just `SBA` + `"<user> <password>"` and a READY
  command is `SBA` + the command text.
- The client does not parse the 3270 order stream — it decodes the whole record
  as CP037 and regexes `PKTR\{...\}` off the result panel.

For a full interactive green screen, point web3270 at `host.docker.internal:8991`
(see "Connecting your own terminal" above), or hand-drive RACF / TSO / ISPF /
SDSF from the `ttyd` link. Vendoring web3270's `tn3270/session.js` into the map
panel itself is still a roadmap follow-up.
