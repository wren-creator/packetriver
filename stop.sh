#!/usr/bin/env bash
# Stop the town.
#   (no args)     stop containers, keep the volumes
#   --all | -v    also remove the named volumes (wipes flags, scoring db, PLC state)
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

load_active_packs
PKT_SEGMENTED=1   # harmless to include if the file isn't actually in use
if ! compose_files; then
  warn "one or more active packs are missing from packs/ - stopping the base town only"
  COMPOSE_FILES=(-f docker-compose.yml)
  [ -f docker-compose.segmented.yml ] && COMPOSE_FILES+=(-f docker-compose.segmented.yml)
fi

case "${1:-}" in
  --all|-v)
    warn "removing containers AND volumes (flags, scoring db, saved PLC logic)"
    dc "${COMPOSE_FILES[@]}" down -v 2>/dev/null || dc -f docker-compose.yml down -v
    ok "town stopped, volumes removed"
    ;;
  *)
    dc "${COMPOSE_FILES[@]}" down 2>/dev/null || dc -f docker-compose.yml down
    ok "town stopped, volumes kept"
    ;;
esac
