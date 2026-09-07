# District: The mainframe tier — Phase 3c / 3d

Two green-screen hosts sit behind the civic web front doors: an **AS/400 (IBM i)**
behind Town Hall for payroll (`as400_empmast`, Phase 3c), and an **IBM z16
(z/OS)** behind First Packet Bank & Trust for core banking (`z16_racf`, Phase
3d). Both are real terminal hosts vendored from
[web3270](https://github.com/wren-creator/web3270) (GPL-3.0); both carry a
handful of curated, genuine bugs rather than a deep OS emulation.

---

## The Packet River AS/400  (`as400_empmast`) — Phase 3c

Behind Town Hall (and, in the story, the Widget Factory) sits an IBM i / AS/400
running payroll on a green screen. It is a real TN5250 host: a SIGNON panel, a
menu tree, DSPMSG, WRKUSRPRF, and Interactive SQL. The mock is vendored from
[web3270](https://github.com/wren-creator/web3270) (GPL-3.0) with one addition —
a `PAYROLL/PAYKEY` file carrying this session's flag, dropped into the same
`PAYROLL` library the box already ships `*PUBLIC *ALL`.

| | |
|---|---|
| Surfaces | TN5250 on `127.0.0.1:8992` (container port 3272). From the map: click **Town Hall**, then **green screen ↗** to open the in-browser terminal (`ttyd` on the player box, `:7681`). |
| The bug | Three stacked IBM i misconfigurations, all real: (1) a **blank password signs you on as any profile** — the mock's long-standing convenience, and exactly what unhardened `QSECURITY 20`-era boxes did; (2) **`QSECOFR` still has its shipped default password** (`QSECOFR`); (3) the **`PAYROLL` library and `EMPMAST` file are `*PUBLIC *ALL`**, so any signed-on profile can read them from SQL. |
| Tool | `as400_5250.py` — a purpose-built TN5250 client on the player box (menu option 1, "AS/400 payroll pull"). Negotiates the 5250 telnet options, signs on, opens `STRSQL`, runs `SELECT * FROM PAYROLL.PAYKEY`, scrapes the flag off the result panel. Option 2 lets you run your own `SELECT * FROM lib.table` (try `QIWS.QCUSTCDT`, `PAYROLL.EMPMAST`). |
| By hand | `telnet`/`tn5250` to `:8992` if you have a client → User `QSECOFR`, Password `QSECOFR` (or any user, blank password) → `STRSQL` on the command line → `SELECT * FROM PAYROLL.PAYKEY`. |
| Physical result | Submitting the flag fires `cityhall_payroll`: Town Hall's `payroll_balance` drops to 0 on the map and `admin_pwned` flips. Same effect the Town Hall web LFI chains into — the payroll money is gone whichever way you got in. |
| Flag location | `PAYROLL/PAYKEY`, column `RECONKEY`, one row. Read at mock startup from `/run/secret/as400_empmast/flag.txt`. |
| Points | base 200, severity `loud`. |
| Reset | reset panel `civic` scope restores Town Hall's balance and announcement. The AS/400 mints a fresh `PAYKEY` row only on a full `scoring` re-run. |
| Hardened build | On a real box: set `QSECURITY` to 40+, require passwords (no blank sign-on), rotate `QSECOFR` off its default and restrict its device access (`QLMTSECOFR`), and pull `*PUBLIC` down to `*EXCLUDE` on `PAYROLL` with an authorization list for the people who actually run payroll. |
| Real-world | Default and blank IBM i credentials (`QSECOFR/QSECOFR`, `QSRV/QSRV`, `QPGMR`) are a standing finding in every AS/400 security review; `*PUBLIC *ALL` on application libraries is the single most common IBM i exposure. TN5250 is cleartext — on a real network this whole exchange, password included, is on the wire. Green-screen depth here is deliberately shallow: a real SIGNON panel and a handful of curated, genuine bugs, not a full OS. |

## Wire notes (for `as400_5250.py`)

The client is small on purpose, in the spirit of `modbus_attack.py`: just enough
5250 to drive the payroll path, not a general-purpose emulator.

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

A full interactive in-browser green screen (vendoring web3270's
`tn5250/session.js` behind a Node CLI renderer) is tracked in the roadmap; the
`ttyd` link on the map already gives a real terminal for hand-driving it once
that lands.

---

## The Packet River IBM z16  (`z16_racf`) — Phase 3d

Behind First Packet Bank & Trust runs core banking on a z/OS LPAR: a real
TN3270E host with a RACF logon panel, TSO READY, ISPF, SDSF, JCL/SUBMIT. The
mock is vendored from web3270's `mock-lpar` (GPL-3.0). One addition: a RACF
command family at the READY prompt — `LISTUSER`, `RLIST`, `SETROPTS LIST` —
and a FACILITY profile, `BANK.XFER.APPROVE`, left in a deliberately weak state
with this session's flag parked in its `INSTALLATION DATA`.

| | |
|---|---|
| Surfaces | TN3270E on `127.0.0.1:8991` (container port 3270). From the map: click **First Packet Bank & Trust**, then **z16 green screen ↗** to open the in-browser terminal (`ttyd` on the player box, `:7681`). |
| The bug | Three real, common RACF review findings: (1) **`IBMUSER` was never revoked** and still holds `SPECIAL OPERATIONS AUDITOR` (`LISTUSER IBMUSER`), and its install-default password `SYS1` still logs on; (2) the `BANK.XFER.APPROVE` FACILITY profile is **`UACC(READ)` and in `WARNING` mode** — a failed access check is logged but *allowed*, so the transfer-approval control is fail-open; (3) globally **`NOPROTECTALL`** with WARNING honored (`SETROPTS LIST`). Someone then stashed a reconciliation key in the profile's world-readable `INSTALLATION DATA`. |
| Tool | `z16_3270.py` — a purpose-built TN3270E client on the player box (menu option 3, "RACF pull"). Negotiates TN3270E, logs on as `IBMUSER`/`SYS1`, runs `RLIST FACILITY BANK.XFER.APPROVE` at READY, scrapes the flag off the command panel. Option 4 runs any READY command you type (`SETROPTS LIST`, `LISTUSER IBMUSER`, `LISTAPF`). |
| By hand | Any TN3270 client to `:8991` → `IBMUSER` / `SYS1` → at `READY` type `RLIST FACILITY BANK.XFER.APPROVE`. |
| Physical result | Submitting the flag fires `bank_drain`: the bank reads `carded`, balance 0, ATM drained, and the grid-tied alarm drops on the map — the same effect as the web JWT-`none` path. WARNING-mode approval means fraudulent transfers sail through. |
| Flag location | The `BANK.XFER.APPROVE` FACILITY profile's `INSTALLATION DATA` field. Read at mock startup from `/run/secret/z16_racf/flag.txt`. |
| Points | base 275, severity `loud`. |
| Reset | reset panel `bank` scope restores the bank. A fresh flag is minted only on a full `scoring` re-run. |
| Hardened build | Revoke `IBMUSER` (or at minimum strip `SPECIAL`/`OPERATIONS` and rotate the password); take `BANK.XFER.APPROVE` out of WARNING mode and set `UACC(NONE)` with an explicit access list; `SETROPTS PROTECTALL(FAILURES)`; and never put secrets in `INSTALLATION DATA` — it is metadata, readable by anyone who can `RLIST` the profile. |
| Real-world | Never-revoked `IBMUSER` with the shipped `SYS1` password is a standing pen-test finding on z/OS. WARNING mode is meant to be a migration aid — profiles left in it for years are a classic audit hit (it silently permits every access it would otherwise deny). `NOPROTECTALL` means any dataset with no covering profile is open. TN3270 is cleartext. Green-screen depth here is deliberately shallow: a real RACF logon and a few genuine misconfigurations, not a z/OS emulator. |

### Wire notes (for `z16_3270.py`)

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
  data. So the logon record is just `SBA` + `"IBMUSER SYS1"` and a READY
  command is `SBA` + the command text.
- The client does not parse the 3270 order stream — it decodes the whole record
  as CP037 and regexes `PKTR\{...\}` off the result panel.

A full interactive in-browser 3270 (web3270's `tn3270/session.js` behind a Node
renderer) is the roadmap follow-up; the `ttyd` link already gives a real
terminal for hand-driving RACF, TSO, ISPF, and SDSF today.
