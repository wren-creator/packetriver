# District: The Packet River AS/400  (`as400_empmast`) — Phase 3c

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
