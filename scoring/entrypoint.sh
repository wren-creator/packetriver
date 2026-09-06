#!/bin/sh
# Generate this session's flags (writes the flag map into scoring.db and drops
# each flag onto the shared pkt-flags volume for its target to plant), then
# start the API.
set -e
python flags.py
exec python -u app.py
