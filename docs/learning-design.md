# Learning design: guidance, not walkthroughs

Packet River is a game you learn by playing. The learning happens when the
player builds the mental model themselves - fingerprints the service, spots the
bug class, picks the tool, works out the payload. A step-by-step "paste this,
then paste this" turns that into a typing exercise and the lesson evaporates.

**The rule:** ship *guidance*. Do not ship a path that hands someone full
control of the town in 30 minutes.

Guidance means: the class of bug, the real-world parallel, the tool family, the
part of the app to look at, the map effect, and - always - the fix. It does not
mean a working command string.

## The help tiers

| Tier | Where | What it gives | Cost |
|---|---|---|---|
| 1 - Orientation | the building's in-game blurb, `docs/districts/*.md` (public), the README teaser | bug class, tool family, real-world parallel, map effect, fix. **No payloads, no exact parameters, no credentials.** | free, always visible |
| 2 - Nudge | an opt-in "hint" action in the UI (wires to `hint_penalty` in the score formula) | a sharper pointer - a parameter name, "the ids start at 1001", a payload *skeleton* with the specifics blanked | docks points |
| 3 - Easter eggs | hidden in-world artifacts (see below) | a fragment: a technique name, one parameter, one fact, a partial payload | free, but you have to find them |
| 4 - Answer key | `instructor/answer-key.md`, `docs/scenarios.md` (instructor), the EPUB | the full transcript, with the fix | instructor-facing, not in the player's UI |

Tiers 1-3 are what a solo player sees. Tier 4 is for the person running a class.

### Keep the public hints honest

`scoring/flags.py`'s `hint` strings and some `docs/districts/*.md` lines are
currently close to complete solutions (e.g. a full `UNION SELECT` with the real
column order and table name). Audit them down to Tier-1 direction; move the
sharp version to `instructor/` or behind the Tier-2 hint-penalty path. The
`location_hint` column in `scoring.db` is an internal breadcrumb - if a future
UI surfaces it, it goes through the Tier-2 penalty, never for free.

## Easter eggs as in-world help

Hiding help in found artifacts fits a game better than a help menu, and it
teaches the habit that matters in a real engagement: **look around.** A stale
`README.old` in a web root, a `.bak` config, a `robots.txt`, a sticky note
baked into a wall texture, a dev comment, an NPC line, a pastebin-style note on
a shared drive - all realistic, all optional, all rewarding to find.

Rules for an egg:

- **Fragments and direction, never a finished line.** An egg may name the
  technique, one parameter, one fact ("receipts start at 1001"), or a payload
  skeleton with the table/column blanked. If it contains a copy-paste command
  that lands the flag, it is a hidden walkthrough - the exact thing this
  document exists to prevent.
- **Optional and lightly rewarded.** Finding an egg can carry a small score
  bump, so seeking help is also play, not a walk of shame.
- **Tunable.** An env knob (`PKT_EGGS=off|subtle|obvious`) lets an instructor
  set how findable they are for a given class.
- **In character.** The egg belongs to the town - something a sloppy admin or
  a chatty resident would actually have left lying around.

Tracked in `ROADMAP.md` under Phase 6 (polish).
