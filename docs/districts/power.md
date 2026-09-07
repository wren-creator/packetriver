# District: Power Substation  (`power_modbus_feeder`) — Phase 2

The substation bus: a main incomer breaker, four feeder breakers (residential,
business, industrial, streetlights), and local generation. Soft-PLC in the
`field-plc` container.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | operator terminal at `http://127.0.0.1:8093/power` (mimic HMI - one-line diagram, breakers, AUTO/HAND) · Modbus/TCP on the field bus (`127.0.0.1:5503`). |
| The bug | unauthenticated, unvalidated Modbus writes (`MODBUS_WRITE_OPEN=1`). The protocol has no auth, and nothing checks the writer — you can open breakers or push generation out of range. |
| Tool | `modbus_attack.py`, or `pymodbus` by hand. |
| Physical result | `PowerModel` reads the breaker coils each tick. Open a feeder and that zone goes dark on the map (houses, streetlights, the business district, the traffic heads via the business feeder). Open the main and the whole town goes dark and the bus frequency dives as the island collapses (60 -> ~56 Hz). |
| Flag | proves you had write access; it only becomes readable while the PLC is in maintenance mode, so you have to write to the PLC to get it. `modbus_attack.py power flag`. |
| Points | base 175, severity `loud`. |
| Reset | reset panel `power` scope, or `modbus_attack.py power restore`. |
| Hardened build | `MODBUS_WRITE_OPEN=0`: the scan loop re-closes the breakers and clamps the setpoint every pass, so an attacker's write gets stomped. |
| Real-world | Ukraine 2015 / 2016 (SCADA operator sessions hijacked, breakers opened remotely), FrostyGoop / Lviv 2024 (Modbus writes to heating-system controllers in winter). Same lesson: the field protocol has no auth; segment it, enforce a source allowlist, monitor for writes. Modbus for the power PLC here is an arm64-safe stand-in for S7comm / DNP3 — the model doesn't care which protocol delivered the coil write. |
