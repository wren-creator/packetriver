# Packet River

A small town you break into for a high score.

Packet River is a browser game wrapped around a real cyber range. One live map
shows a whole town running normally: traffic cycling through four crossroads, a
train on its loop, water and power flowing to the houses, a clean river with
people swimming in it. Every building on that map is also a real, deliberately
vulnerable service you can scan and attack with the same open-source tools you
would use on a real engagement. Land an exploit, pull the flag hidden inside
it, submit it, and watch the town break on screen: raw sewage into the river,
houses going dark and dry, the payroll drained, the rail switch thrown into the
widget factory. Then hit reset and try to do it again, faster, or quieter.

It is the third in a family with [Widgetorium](https://github.com/wren-creator/widgetorium)
(a vulnerable web app lab) and [Cross Creek](https://github.com/wren-creator/crosscreek)
(an ICS/OT range). Same idea, learn by doing, except this one keeps score.

> **Authorised use only.** Packet River ships wired with real, working
> weaknesses. Run it only on a machine you control. Never point a Packet River
> command, script, payload, scan, or credential at a system you do not own.
> Some of these attacks have physical consequences in the real world. This game
> exists so you never have to learn that on a live one. `start.sh` refuses to
> launch if any port would bind past `127.0.0.1`, and the attacker box has no
> route off the lab.

## How to play

```
./setup.sh      # one-time: preflight, build images
./start.sh      # bring the town up
./status.sh     # health + loopback + containment audit
```

Then open **http://127.0.0.1:8080/**, sign up, and start a run. The map is the
town of Packet River (pop. 646). Click any building and its real service opens,
starting with a login portal, the same as the Cross Creek HMIs and the
Widgetorium login. Get past it, scan, break something, find the flag, submit
it. Your score goes up, the map degrades, and the leaderboard updates. The
reset panel puts any building, or the whole town, back to golden state.

```
./reset.sh              # restore everything to golden state
./start.sh --segmented  # the hardened town: run your attacks again and watch them fail (Phase 4+)
./stop.sh               # shut down
```

## The town

| District | What is there | What breaks |
|---|---|---|
| Main Street | 8 storefronts: General Store, Hardware, Pharmacy, Diner/Cafe, Barbershop, Tavern, Dry Cleaners, Bait & Tackle | defaced, database dumped, customers carded |
| First Packet Bank & Trust | online banking, an ATM, an alarm panel wired to the power grid | money moved, ATM drained, alarm cut |
| Town Hall | public announcements, payroll portal, card payments | site defaced, payroll drained |
| Water treatment | operator HMI + a soft PLC | mains pressure lost, houses go dry, a main bursts |
| Sewage plant | operator HMI + a soft PLC | bypass opened, raw sewage down the river to the swimming beach |
| Power substation | operator HMI + a soft PLC | feeders tripped, houses and streetlights dark, frequency sags |
| Traffic control | 4 crossroads + an open message broker | lights hijacked to all-green, crashes |
| Rail | loop track + a switch into the widget factory | switch thrown, train derailed, factory fire |
| Police & Fire | dispatch screens, alarm panels | minor targets, one bug each |
| Local Diner Wi-Fi | an open, unencrypted network | a different lane: sniff cleartext credentials off the air |

Exactly one bug class per storefront, so no two teach the same thing. Every
scenario in `docs/scenarios.md` carries a real incident or CVE reference and a
fix. The map is pixel-art isometric with a live overlay for everything that
lights up, floods, or goes dark.

Packet River gives you *direction*, not a script. The building blurbs and the
district docs tell you the bug class, the tool, and the fix; they do not hand
you a working payload. Stuck? There is an opt-in hint that costs points, and
hidden notes scattered around the town that cost only the looking. See
[`docs/learning-design.md`](docs/learning-design.md).

## Requirements

Docker with Compose v2 (or v1), and about 1 GB of free memory for the full
town. `PKT_LIGHT=1` in `.env` skips the bundled attacker box and the IDS if you
would rather attack from your own shell.

## Status

Early build. See `ROADMAP.md`. **Phases 0-3** are in:

- the pixel-art live map with its overlay
- all of **Main Street** (8 storefronts, one bug class each), **Town Hall**,
  **Police**, **Fire**, the **payment gateway**, and **First Packet Bank &
  Trust**, each behind its login portal
- the **water, power, and widget-factory** districts on real Modbus, with an
  operator HMI
- an **AS/400** behind Town Hall (TN5250) and an **IBM z16** behind the Bank
  (TN3270), both real green screens with curated bugs
- the score / run / leaderboard loop, the reset panel, and the boxed-in
  attacker box with a browser terminal

Sewage, traffic, rail, the Alert-Level meter, the blue-team response, and the
Wi-Fi lanes land over Phases 4-6. Overlay alignment against the map art has a
drag-and-copy editor (`?edit=1`, see `docs/overlay-editing.md`); a final pass
waits for the Phase 6 art.

## More

- Community and discussion: **britleydev.slack.com**
- Consulting, training, and talks: **https://britleyhoffconsulting.com**,
  **britleyhoff@britleyhoffconsulting.com**
- Source: **https://github.com/wren-creator/packetriver**

If Packet River is useful to you, there is a tip jar in the corner of the map.
No pressure, and it never gates anything in the game.

## Licence

GNU GPL-3.0. See `LICENSE`.
