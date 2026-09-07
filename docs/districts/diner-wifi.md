# District: The Diner's open Wi-Fi  (`diner_wifi`) — Phase 5a

The Packet River Diner runs an open guest network with no encryption anywhere.
This is a **layer-2 lane**, a different skill from the web and OT districts:
you don't break a login, you get between two hosts and read what was never
protected.

Honest scope: Docker has no radio, and shipping something that de-authenticates
real access points would be irresponsible. `lan-net` is a **switched LAN
standing in for open 802.11**. The lesson (unencrypted traffic on a shared
medium is readable and MITM-able) is the same; the RF layer is a real wireless
course, not this repo.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | the Diner Wi-Fi segment `172.31.60.0/24` (the `player` box is on it). `netlab` at `.10` serves a cleartext rewards portal (HTTP :80) and a toy POP3 (:110); `netlab-patron` at `.20` signs in and reads mail over the segment every few seconds. |
| The bug | nothing on the segment is encrypted, and there's no client isolation. A switch won't hand you another host's unicast, so passive sniffing sees nothing, but an ARP-spoof MITM puts you in the path, and then the patron's portal login and their whole inbox are in the clear. |
| Tool | `arpspoof` (dsniff) + `tcpdump`, or `wifi_sniff.py` which scripts both. |
| Physical result | `shop_carded`, the Diner reads `carded` on the map. A sustained ARP spoof also flips a neighbour's MAC in `netlab`'s ARP cache; it publishes a bus event that adds Alert heat, enough to cross Level 1. Noisy layer-2 is noisy. |
| Flag | in the one message in the patron's POP3 inbox (the "reconciliation code"). Read at `netlab` startup from `/run/secret/diner_wifi/flag.txt`. |
| Points | base 125, severity `medium`. |
| Reset | reset panel `diner` scope. A fresh flag is minted on a full `scoring` re-run. |
| Hardened build | WPA2-Enterprise (or at least client isolation / a private VLAN per client), and TLS on the portal and the mail service so a MITM yields ciphertext. `docker-compose.segmented.yml` is the working counter-build. |
| Real-world | credential theft off open/hotel/coffee-shop Wi-Fi is a standing risk; ARP spoofing on a switched LAN (CWE-300, MITRE T1557.002) is the same move once you're associated. POP3/HTTP without TLS puts the password and the mail body on the wire (T1040). |

## What the player box has

`player` is on `lan-net`, carries `tcpdump` and `dsniff`, has `NET_ADMIN` +
`NET_RAW`, and `net.ipv4.ip_forward=1` is set by the compose file (a namespaced
sysctl, not `--privileged`) so the MITM forwards rather than black-holing the
patron's traffic.
