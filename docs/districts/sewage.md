# District: Sewage Treatment  (`sewage_modbus`) — Phase 4

The plant that treats the town's wastewater and returns it to the river: an
aeration basin, disinfection dosing, a treated-return pump, and a storm-bypass
gate that should never sit open. Fourth soft-PLC in the `field-plc` container.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

| | |
|---|---|
| Surfaces | operator terminal at `http://127.0.0.1:8093/sewage` (mimic HMI - pumps, aeration, bypass gate, AUTO/HAND) · Modbus/TCP on the field bus (`127.0.0.1:5505`). |
| Front door | the plant's operator terminal. Each plant has its own operator login, minted fresh at boot and rotated on policy (the blue team rolls the set at Alert L2). The current values are on the unauthenticated shift-handover sheet the ops team left on the box (`/ops/handover.txt`). Getting in is not the scored bug - the Modbus bus is - but it is a small finding of its own. |
| The bug | unauthenticated, unvalidated Modbus writes (`MODBUS_WRITE_OPEN=1`). Open the storm bypass, or stop aeration and dosing — nothing checks the writer. |
| Tool | `modbus_attack.py`, or `pymodbus` by hand. |
| Physical result | `simmap`'s `SewageModel` reads the coils each tick. With the bypass open (or aeration + dosing off) the effluent-quality index collapses, `effluent_path` flips to `raw`, and the outfall line on the map turns algae-green. Over the next ~10 s `river_contamination` ramps up, the plume spreads down toward the swimming beach, and the swimmers turn sick. |
| Flag | proves you had write access; it only becomes readable while the PLC is in maintenance mode, so you have to write to the PLC to get it. `modbus_attack.py sewage flag`. |
| Points | base 175, severity `loud`. |
| Reset | reset panel `sewage` scope, or `modbus_attack.py sewage restore`. |
| Hardened build | `MODBUS_WRITE_OPEN=0`: the scan loop re-closes the bypass, re-starts aeration / dosing / the return pump, and clamps the dose setpoint every pass. |
| Real-world | Sanitary-sewer overflows and deliberate bypasses are a standard enforcement issue; an attacker with write access to the plant PLC can force one on demand. Same lesson as water and power: the field protocol has no auth — segment it, enforce a source allowlist, monitor for writes. CISA CPGs; EPA WCA. Modbus here is an arm64-safe stand-in for whatever protocol the real plant runs. |
