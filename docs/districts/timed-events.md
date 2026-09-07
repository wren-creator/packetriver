# Timed events — a town that moves on its own

Without these, Packet River only changes when you break something. Timed events
give it a clock, a reason to hurry, and a reason to clean up after yourself.

Controlled by `PKT_EVENTS` in `.env`: `off`, `calm` (default), or `lively`.
`calm` leaves 5 to 9 minutes between events; `lively` leaves 2 to 4. Each event
runs for a fixed window, then reschedules itself. Instructors can fire one on
demand: `POST /api/debug/event {"name": "...", "action": "start|end"}`.

The current schedule and any active event ride in every state snapshot under
`events`, and each start/stop is published on `pkt/sim/event/<name>`.

## The events

### News crew (`news_crew`, 90 s)

A TV crew parks at whatever is most broken right now (or Town Hall if nothing
is). While they are filming, **any Alert heat from an incident on that
subsystem is multiplied by 1.6**, getting caught loud on camera is worse than
getting caught loud. The map shows a camera over the building in focus.

If nothing is broken when the crew arrives, they film Town Hall and there is no
multiplier until something on that subsystem breaks.

### State inspector (`inspector`, 75 s)

An inspector arrives for a fixed window. What happens on their way out depends
on the state of the town:

| At arrival | At departure | Result |
|---|---|---|
| all clear | all clear | nothing |
| all clear | something is broken | **+45 heat**, a citation logged to the SOC feed |
| already broken | still broken | +20 heat, "findings noted" |

So an incident you start *during* an inspection is the worst-case timing, and
one you clean up before the inspector leaves costs nothing. It rewards stealth
and it rewards tidying up.

### Founder's Day parade (`parade`, 60 s)

Parade crowds fill the crossroads. A signal hijacked to ALL-GREEN **during the
parade racks up crashes about four times as fast** (the crash counter ticks
twice as often and adds two each time). Same exploit, far bigger consequence,
if you time it for the parade. A timing puzzle rather than a plain toggle.

## Reset

`reset events` (or `reset all`) clears the schedule and any active event and
starts the clock over.
