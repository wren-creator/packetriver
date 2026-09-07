# District: Recon — the municipal name server  (`dns_axfr`) — Phase 4.5

Every other district hangs off a `127.0.0.1:<port>`. This one gives the town a
name space. A `dns` container (CoreDNS) is the `player` box's only resolver: it
is authoritative for `packetriver.range` and forwards everything else to
Docker's embedded DNS, so bare container names still resolve too.

The names are **CNAMEs onto the container network** (`water.packetriver.range`
→ `packetriver-field-plc.`), so `dig`, `nslookup`, `curl`, and
`nmap water.packetriver.range` all follow through to the real service. You do
recon by business name from here on, not by memorising ports.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | the resolver at `172.31.20.253:53` (the `player` box already points here, `dns:` in compose). From the map there is nothing to click; this is a `player`-box lane. |
| The bug | the zone answers **AXFR (zone transfer) from anyone**. One request enumerates every host in town, and turns up a TXT record for a box that was supposed to be decommissioned, with a maintenance token parked in it. |
| Tool | `recon.py dns`, or `dig axfr packetriver.range @dns`, or any resolver library's transfer call. |
| Physical result | none, pure recon. `effect: noop`; nothing on the map moves. |
| Flag | in a stray `TXT` record (`scada-legacy-07.packetriver.range`) that is only reachable by pulling the whole zone. Read at `dns` startup from `/run/secret/dns_axfr/flag.txt`. |
| Points | base 75, severity `quiet`. |
| Reset | nothing to reset; a fresh flag is minted only on a full `scoring` re-run. |
| Hardened build | restrict `transfer { to ... }` to known secondaries (or drop it), and split an internal view from an external one so a public resolver never carries the internal host list. |
| Real-world | Open AXFR is one of the oldest external-recon wins there is: a single `dig axfr` against a misconfigured secondary hands over every internal hostname, and stale records for "retired" kit routinely outlive the kit. Fix: `allow-transfer` allowlists, split-horizon DNS, and don't store secrets in DNS. |

## The name table

Common name (map hover) · official name · `*.packetriver.range` label:

| Map | Official name | Name |
|---|---|---|
| Water treatment | Packet River Municipal Water Authority | `water` |
| Sewage plant | Packet River Water Reclamation Facility | `reclamation` |
| Power substation | Packet River Power & Light, Substation 1 | `power` |
| Widget Factory | Packet River Widget Works | `widgetworks` |
| Traffic control | Packet River DOT, Signal Operations | `signals` |
| Rail control | Packet River & Southern Railroad, Dispatch | `dispatch` |
| First Packet Bank | First Packet Bank & Trust | `firstpacketbank` |
| z16 core banking | FPB&T Core Banking (z/OS) | `core.firstpacketbank` |
| AS/400 payroll | Packet River Payroll Bureau (IBM i) | `payroll` |
| Payment gateway | Packet River Merchant Services | `merchant` |
| Town Hall | Town of Packet River, Borough Hall | `townhall` |
| Police | Packet River Police Department | `pd` |
| Fire | Packet River Fire & Rescue | `fd` |
| General Store | Packet River General Store | `generalstore` |
| Hardware | Riverside Hardware & Supply | `hardware` |
| Pharmacy | Packet River Pharmacy | `pharmacy` |
| Diner | The Packet River Diner | `diner` |
| Barbershop | Riverbend Barber & Salon | `barber` |
| Tavern | The Broken Packet Tavern | `tavern` |
| Dry Cleaners | Packet River Cleaners | `cleaners` |
| Bait & Tackle | Packet River Bait & Tackle | `baittackle` |

The Main Street shops and the civic sites CNAME onto `packetriver-gateway`,
which routes each `<name>.packetriver.range` to its subdirectory of the one
shared `websites` container and hands each a distinct `Server` /
`X-Powered-By` (real shared hosting, told apart at the app layer). The
backend's own Apache 404 page still leaks under that mask.

More recon surface:

- **Reverse DNS.** `recon.py rev` (or `dig axfr 20.31.172.in-addr.arpa @dns`)
  dumps a PTR for every box the name server knew at boot. Cross-check it
  against the forward zone.
- **`/directory`** and **`/whois?q=<name>`** on the map server: a plain
  municipal directory listing every official name and its hostname, and a
  toy whois-over-HTTP.

## No cross-portal navigation

A portal stands alone. The field-plc operator HMI no longer has a nav bar
linking the other three plants, and `GET /` no longer lists the four portals:
an unknown or bare host gets a 404, and a known plant hostname
(`water` / `reclamation` / `power` / `widgetworks` `.packetriver.range`) is
redirected straight to that one plant's login, nothing else. You reach each
target from the map or from recon by name, never by following a link out of a
portal you already popped. That is what makes per-item recon the point rather
than a formality.
