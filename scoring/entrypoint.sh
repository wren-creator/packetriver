#!/bin/sh
# Phase 0: nothing to generate yet (no targets). Phase 1 adds:
#   python flags.py generate   # mint per-session flags, write /run/secret/*, seed scoring.db
set -e
exec python -u app.py
