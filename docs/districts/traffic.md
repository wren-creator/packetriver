# District: Traffic Control  (`traffic_mqtt`) — Phase 4

Five crossroads, each a signal controller. The controllers take their commanded
mode off the event bus; the green/red auto cycle and the crash counter live in
`simmap`. Container: `traffic-plc`.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | read-only signal status at `http://127.0.0.1:8095/` · the MQTT bus at `127.0.0.1:1883`. |
| The bug | on the flat broker the controllers' command topic has **no ACL and no auth** — anything that can reach the bus can force a crossroads to ALL-GREEN. A separate "engineering mode" topic takes a short PIN and, on a match, publishes the flag. |
| Tool | `mosquitto_pub` / `mosquitto_sub`, or `traffic_attack.py`. |
| Physical result | `simmap` mirrors each intersection's commanded mode. On ALL-GREEN the map's signal dot locks green, the intersection pulses "hijacked", and the crash counter climbs a few seconds later; downtown gridlocks. |
| Flag | published on the engineering-mode flag topic once the PIN is accepted. |
| Points | base 175, severity `loud`. |
| Reset | reset panel `traffic` scope (also clears the retained flag), or `traffic_attack.py restore`. |
| Hardened build | `docker-compose.segmented.yml` swaps in a broker `acl_file` + password file: each `pkt/*` topic is locked to its rightful publisher and `pkt/traffic/#` is password-gated, so the anonymous publish is refused. |
| Real-world | Unauthenticated MQTT brokers exposed to the internet are a standing Shodan finding, and traffic-signal and roadside-ITS controllers have repeatedly shipped with default or absent auth (Cesar Cerrudo's Sensys Networks work, the 2014 University of Michigan traffic-signal study). Fix: broker ACLs + auth, signed commands, and keep the control bus off any routable path. |
