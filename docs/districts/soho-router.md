# District: The SOHO router pivot  (`soho_router_pcap`) — Phase 5b

A house on the edge of town runs a consumer router. The homeowner is a Packet
River & Southern rail engineer who works from the couch. This lane is the
**APT remote-worker pivot**: residential foothold to OT, which nothing else in
the range covers.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | `soho-router` (PacketLink HR-24) on `172.31.61.10`, admin panel on HTTP :80, reachable from the town LAN (`it-net`). Behind it, `home-net` `172.31.61.0/24` with `soho-resident` at `.20`. The rail maintenance console at `rail-plc:2323` is the pivot target. |
| The bug | three, all common on consumer gear: **WAN-side admin is reachable** (not just from the home LAN); the admin login is still the shipped **admin / admin**; and the built-in **Diagnostics packet-capture** returns a decoded dump of home-LAN traffic. The resident signs in to a rail crew portal over plain HTTP on a loop, so the capture holds their credential, which is **reused** on the rail console. |
| Tool | a browser or `curl` for the router; `soho_pcap.py` scripts it; `nc` for the rail console replay. |
| Physical result | the `soho_router_pcap` flag itself is recon (`noop`, no map change). Replaying the sniffed operator credential on `rail-plc:2323` chains into `rail_console`, `flag` returns that flag, and `set switch spur` before the train reaches the branch derails it into the Widget Factory. |
| Flag | an `X-Reconcile:` header in the decoded response inside the router's packet capture. Read at `soho-router` startup from `/run/secret/soho_router_pcap/flag.txt`. |
| Points | base 150, severity `medium`. |
| Reset | nothing to reset for the recon flag; use the `rail` scope for the chained derail. |
| Hardened build | disable WAN-side administration, force a credential change off `admin/admin` at first login, put the crew portal behind TLS, and **don't reuse operator credentials** between a web portal and a device console. Segmentation should stop a residential IP reaching the rail console at all without a hardened VPN. |
| Real-world | Volt Typhoon and friends have leaned on SOHO routers as footholds; default credentials on consumer gear are CWE-1392 / MITRE T1078.001; the capture-page abuse is T1040; the credential reuse into OT is T1078 again, and the SOHO -> OT path via a remote worker is exactly the concern behind CISA's remote-access guidance. |

## The chain

1. `admin` / `admin` into the router's WAN-side admin (`soho_pcap.py` step 1).
2. Diagnostics → packet capture → the decoded dump has the resident's
   `POST /portal/rail/login` with `user=` / `pass=` and the `X-Reconcile`
   flag. Submit the flag.
3. The sniffed credential is a real operator account on `rail-plc:2323`.
   `login` with it, `flag` for the `rail_console` flag, `set switch spur` for
   the derail.
