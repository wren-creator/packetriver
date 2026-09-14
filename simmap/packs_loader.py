"""Expansion-pack loader: validates and merges pack content into the
running simmap process at boot.

Packs (see packs/README.md) are never committed to this repo - they're
dropped into packs/<name>/ and bind-mounted read-only here at /app/packs.
PKT_PACKS (set by start.sh --pack <name>) names which ones are active.

Called once, early, from run.py and wsgi.py. Every problem here is a fatal
boot error - printed and the process exits (so the container's healthcheck
never goes green) - not a silently missing map badge or effect discovered
mid-game.
"""
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys

PACKS_DIR = pathlib.Path("/app/packs")


def active_pack_names() -> list[str]:
    return [n for n in os.environ.get("PKT_PACKS", "").split(",") if n]


def pack_prefix(name: str) -> str:
    return name.replace("-", "_") + "_"


def _fatal(msg: str) -> None:
    print(f"[packs] FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_effects(base_effects: dict) -> None:
    """Merge each active pack's simmap_effects.py EFFECTS dict into
    base_effects (effects.EFFECTS) in place."""
    for name in active_pack_names():
        prefix = pack_prefix(name)
        mod_path = PACKS_DIR / name / "simmap_effects.py"
        if not mod_path.is_file():
            _fatal(f"pack '{name}' has no simmap_effects.py at {mod_path}")
        spec = importlib.util.spec_from_file_location(f"pack_{name}_effects", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for eid, fn in getattr(mod, "EFFECTS", {}).items():
            if not eid.startswith(prefix):
                _fatal(f"pack '{name}' effect '{eid}' must be prefixed '{prefix}'")
            if eid in base_effects:
                _fatal(f"pack '{name}' effect '{eid}' collides with an "
                       "existing effect id")
            base_effects[eid] = fn


def load_all() -> None:
    """Validate + merge every active pack. No-op if PKT_PACKS is unset."""
    if not active_pack_names():
        return
    import effects
    import server

    load_effects(effects.EFFECTS)
    try:
        server.validate_packs()
    except Exception as exc:
        _fatal(str(exc))
    print(f"[packs] loaded: {', '.join(active_pack_names())}")
