# District: Rail Control  (`rail_console`) — Phase 4

The controller for the loop-track switch and the spur into the Widget Factory.
Container: `rail-plc`. The switch position it holds is published on the bus;
`simmap` reads it and moves the train. Throw the switch to the spur as the
train reaches the branch and it derails into the factory, which catches fire.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | read-only switch status at `http://127.0.0.1:8096/` · a raw-TCP "maintenance console" at `127.0.0.1:2323`. From the map: click **Railroad Control** (SE of the Police Station). |
| The bug | two, stacked: the console has **default credentials**, and its `set label` command hands your input **straight to a shell** — so it is a command-injection foothold, not a label field. Either one reads the maintenance key; `set switch spur` throws the switch. |
| Tool | `nc` / `telnet`, or `rail_attack.py`. |
| Physical result | `simmap` mirrors the switch position. With it set to `spur` when the train crosses the branch, `rail.derailed` latches, the train stops on the spur, and `factory.on_fire` is set — a fire ring on the Widget Factory. |
| Flag | printed by the `flag` command to any signed-on console (and reachable via the injection: `set label ; cat /run/secret/rail_console/flag.txt`). |
| Points | base 200, severity `loud`. |
| Reset | reset panel `rail` scope (switch back to loop, derail cleared), or `rail_attack.py loop`. |
| Hardened build | `docker-compose.segmented.yml` rotates the console credentials; a real fix drops the raw console entirely or puts it behind authentication + a source allowlist, and never shells out on operator input. |
| Real-world | Rail and transit signalling has a long tail of unauthenticated serial-over-IP consoles and telnet management ports; command injection through an "operator input" field that gets concatenated into a shell call is one of the most common embedded-device bugs (CWE-78). The Lodz tram incident (2008) is the canonical "someone threw the switches" story. |
