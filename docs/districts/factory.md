# District: The Widget Works  (`factory_modbus`, `factory_snmp`) — Phase 3b / G

The widget factory has two ways in and a habit of catching fire.

Direction, not a walkthrough (see [`../learning-design.md`](../learning-design.md)).
Step-by-step: [`../../instructor/answer-key.md`](../../instructor/answer-key.md).

## `factory_modbus` — the process plane

| | |
|---|---|
| Surfaces | the widget-factory soft-PLC on Modbus/TCP `127.0.0.1:5504` (container `504`), part of `field-plc`. |
| The bug | unauthenticated Modbus writes. The safety interlocks (e-stop, line run/stop, the hopper gate) are just coils and nothing checks the writer. The flag block unlocks in maintenance mode. |
| Tool | `pymodbus` / `modbus_attack.py`. |
| Physical result | line jam / unsafe run, the Widget Works shows a trouble ring and throughput craters. |
| Points / severity | base 175 / loud. |
| Hardened build | `MODBUS_WRITE_OPEN=0`, the PLC re-asserts golden every scan. Real fix: segment OT, source-allowlist, keep the safety function on a separate non-writable system. |

## `factory_snmp` — the management plane

| | |
|---|---|
| Surfaces | the "line-management" SNMP agent on `udp/161` (`127.0.0.1:1161` on the host), container `factory-snmp`. |
| The bug | the shipped community strings are still in place: `public` reads the whole line-management subtree (`.1.3.6.1.4.1.53864.1`), and a **read-write** community (`private`) lets you set the line-enable OID and stop the line from the enterprise side. The reconciliation key is one of the OIDs. `sysLocation` carries a ticket-number breadcrumb. |
| Tool | `snmpwalk` / `snmpget` / `snmpset`, or `snmp_attack.py` (`walk` / `flag` / `stop` / `start`). |
| Physical result | setting `lineEnable=0` publishes `pkt/factory/cmd`; `simmap` stops the line on the map, same end state as the Modbus path, a different plane. |
| Flag | the `opsNote` OID (`...53864.1.3.0`), readable with `public`. Read at `factory-snmp` startup from `/run/secret/factory_snmp/flag.txt`. |
| Points / severity | base 150 / medium. |
| Reset | reset panel `factory` scope, or `snmp_attack.py start`. |
| Hardened build | `SNMP_HARDENED=1`, the write community is removed and the read community moves off `public`. Real fix: SNMPv3 with auth+priv, no default communities, and no write access from the enterprise network. |
| Real-world | default SNMP community strings (`public` / `private`) on OT and network gear are a standing Shodan / pen-test finding (CWE-1392); a writable community on a line controller is `snmpset` away from a process stop. MITRE ATT&CK for ICS T0855 (unauthorized command message), T0813 (denial of control). |

## The derail pile-up

If a rail car is being loaded (the hopper gate is open) at the moment the train
is routed onto the spur and derails into the factory, it is a pile-up rather
than a stopped line: throughput hard-zeros and the line jams on top of the
fire. Time the `rail_console` derail against the loading cycle for the worst
outcome.
