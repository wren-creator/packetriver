# District: Water Treatment & Distribution  (`water_modbus_pump`) — Phase 2

The Packet River Water Company: an intake, a high-lift pump that pressurises
the distribution main, chlorine dosing, and a tower. Runs on a soft-PLC in the
`field-plc` container.

| | |
|---|---|
| Surfaces | operator HMI at `http://127.0.0.1:8093/` (login portal, `operator` / `operator`, read-only status) · Modbus/TCP on `127.0.0.1:5502` (container port 502) |
| Front door | the HMI portal. Getting in is not the bug; it just shows you the plant. |
| The bug | Modbus writes are accepted from any source with no authentication or validation (`MODBUS_WRITE_OPEN=1`). Stop the high-lift pump (`write_coil 1 0`), close the main valve, crater the pressure setpoint, or zero the chlorine dose. |
| Tool | `modbus_attack.py water stop-pump` (or `pymodbus` / `mbtget` by hand) |
| Physical result | `simmap`'s `WaterModel` reads the pump coil each tick; with the high-lift pump off the distribution pressure bleeds from ~62 psi to zero over a few seconds. `houses_supplied` drops to 0, every house on the map loses its water drop, `water.quality` -> `dry`. Chlorine off -> `quality` -> `brown`. |
| Flag location | input registers `100..131`. The scan loop only fills that block while coil `8` (maintenance mode) is set, so you must write to the PLC to read the flag: `modbus_attack.py water stop-pump && modbus_attack.py water flag`. Planted from `/run/secret/water/flag.txt`. |
| Points | base 175, severity `loud` (Alert +25). Solving power in the same run adds the chain bonus. |
| Reset | the reset panel's `water` scope (or `modbus_attack.py water restore`) writes the golden coils and setpoints back and clears maintenance mode. |
| Hardened build | `MODBUS_WRITE_OPEN=0`: the 0.3 s scan loop re-asserts the pumps and clamps the setpoints every pass, so the same writes get stomped. Run it, watch the attack fail. |
| Real-world | Aliquippa PA 2023 (a municipal water booster station's Unitronics PLC, internet-exposed, default password), Oldsmar FL 2021 (remote HMI, chemical setpoint changed). Modbus has no authentication in the protocol; the fix is network segmentation, an allowlist at the PLC, and taking the HMI off any routable path. CISA CPGs; ISA/IEC 62443. |
