# Expansion packs

Packet River's base town is free and self-contained. Expansion packs add new
districts, services, and bug classes on top of it, purchased and shipped
separately, and never merged into this repo.

## Install a pack

1. Get the pack (its own git repo, cloned or unzipped).
2. Drop it in here as `packs/<name>/`, e.g. `packs/grain-coop/`.
3. Run `./setup.sh` again - it folds the pack's own `.env.pack.example`
   defaults into your `.env` (existing values are never overwritten).
4. Start the town with the pack layered in:
   ```
   ./start.sh --pack <name>
   ```
   Repeat `--pack <name>` to run more than one pack at once. `./stop.sh` and
   `./reset.sh` remember which packs were active (see
   `.packetriver-active-packs`) so you don't have to retype the flag.

Nothing under `packs/` except this file is tracked by this repo's git
history - a pack you drop in stays exactly as its own repo, and removing its
directory removes it from the town on your next `./start.sh` (with no
`--pack` flag for it).

## What a pack looks like

Every pack is self-contained: its own compose fragment, its own scoring and
map fragments, its own vulnerable service(s), and its own training material
(district doc, instructor answer key, easter eggs). None of that is copied
into or shared with this repo's `docs/`, `instructor/`, or `eggs/` - a
purchaser gets everything they need bundled with the pack itself.

```
packs/<name>/
├── README.md
├── docker-compose.yml
├── docker-compose.segmented.yml   # optional: hardened variant
├── .env.pack.example
├── scoring.techniques.json
├── overlay.pack.json
├── simmap_effects.py
├── simmap_model.py                # optional: only if it needs real physics
├── <service>/                     # the vulnerable target(s) themselves
└── docs/
    ├── <name>.md                  # Tier-1 district doc
    ├── answer-key.md              # this pack's own instructor key
    └── eggs.md                    # optional
```

## Naming rule (why two packs never collide)

Every technique id, map-building id, and effect name a pack defines **must**
be prefixed with the pack's own directory name (dashes become underscores),
e.g. a pack at `packs/grain-coop/` uses ids like `grain_coop_cip_writeauth`.
This is checked automatically at boot - a pack that violates it, or that
collides with an existing id, fails the town's health check immediately
rather than silently breaking a flag or a map badge mid-game.

## Currently available

- **Grain Co-op (Vendor Dialects)** - a grain elevator controller on real
  EtherNet/IP (CIP), the base town's first non-Modbus field protocol.
  Repo: `packetriver-pack-grain-coop`. `./start.sh --pack grain-coop`.
