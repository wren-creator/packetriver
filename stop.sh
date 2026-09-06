#!/usr/bin/env bash
# Stop the town.
#   (no args)     stop containers, keep the volumes
#   --all | -v    also remove the named volumes (wipes flags, scoring db, PLC state)
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

FILES=(-f docker-compose.yml)
[ -f docker-compose.segmented.yml ] && FILES+=(-f docker-compose.segmented.yml)

case "${1:-}" in
  --all|-v)
    warn "removing containers AND volumes (flags, scoring db, saved PLC logic)"
    dc "${FILES[@]}" down -v 2>/dev/null || dc -f docker-compose.yml down -v
    ok "town stopped, volumes removed"
    ;;
  *)
    dc "${FILES[@]}" down 2>/dev/null || dc -f docker-compose.yml down
    ok "town stopped, volumes kept"
    ;;
esac
