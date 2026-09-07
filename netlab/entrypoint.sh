#!/bin/sh
set -eu
if [ "${ROLE:-ap}" = "patron" ]; then
    exec python patron.py
fi
exec python ap.py
