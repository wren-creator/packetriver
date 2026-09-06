# District: Power Substation  (`power_modbus_feeder`) — Phase 2

The substation bus: a main incomer breaker, four feeder breakers (residential,
downtown, industrial, streetlights), and local generation. Soft-PLC in the
`field-plc` container.

| | |
|---|---|
| Surfaces | operator HMI at `http://127.0.0.1:8093/` (shared with water) · Modbus/TCP on `127.0.0.1:5503` (container port 503) |
| The bug | unauthenticated, unvalidated Modbus writes (`MODBUS_WRITE_OPEN=1`). Open any feeder breaker (`write_coil 1..4 0`), open the main incomer (`write_coil 0 0`), or push the generation setpoint out of range. |
| Tool | `modbus_attack.py power trip <residential\|downtown\|industrial\|streetlights>`, `modbus_attack.py power trip-main` |
| Physical result | `PowerModel` reads the breaker coils each tick. Open a feeder and that zone goes dark on the map (houses, streetlights, the downtown lights, the traffic heads via the downtown feeder). Open the main and the whole town goes dark and the bus frequency dives as the island collapses (60 -> ~56 Hz). |
| Flag location | input registers `100..131`, gated by the maintenance-mode coil `8` - `modbus_attack.py power trip industrial && modbus_attack.py power flag`. From `/run/secret/power/flag.txt`. |
| Points | base 175, severity `loud`. |
| Reset | reset panel `power` scope, or `modbus_attack.py power restore`. |
| Hardened build | `MODBUS_WRITE_OPEN=0`: the scan loop re-closes the breakers and clamps the setpoint every pass. |
| Real-world | Ukraine 2015 / 2016 (SCADA operator sessions hijacked, breakers opened remotely), FrostyGoop / Lviv 2024 (Modbus writes to heating-system controllers in winter). Same lesson: the field protocol has no auth; segment it, enforce a source allowlist, monitor for writes. Modbus for the power PLC here is an arm64-safe stand-in for S7comm / DNP3 - the model doesn't care which protocol delivered the coil write. |
