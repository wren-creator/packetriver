#!/usr/bin/env bash
# Restore Packet River to golden state: fresh flags, nominal town, clean
# scoreboard run state. This is the "reset all" hammer; the in-game reset
# panel does per-subsystem restores over pkt/reset without a container bounce.
#   -y   skip the confirmation prompt
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

require_docker

if [ "${1:-}" != "-y" ]; then
  printf '%s' "Restore Packet River to golden state (new flags, nominal town, clear run state)? [y/N] "
  read -r ans
  case "$ans" in y|Y|yes|YES) ;; *) info "cancelled"; exit 0 ;; esac
fi

load_active_packs
PKT_SEGMENTED=0
if dc -f docker-compose.yml -f docker-compose.segmented.yml ps --format '{{.Name}}' 2>/dev/null \
     | grep -q packetriver-ids; then
  PKT_SEGMENTED=1
fi

if ! compose_files; then
  warn "one or more active packs are missing from packs/ - resetting the base town only"
  COMPOSE_FILES=(-f docker-compose.yml)
  [ "$PKT_SEGMENTED" = "1" ] && [ -f docker-compose.segmented.yml ] && COMPOSE_FILES+=(-f docker-compose.segmented.yml)
fi

info "down -v"
dc "${COMPOSE_FILES[@]}" down -v

info "rebuild + up"
if ! assert_loopback_only "${COMPOSE_FILES[@]}"; then
  bad "loopback guard failed, not restarting"
  exit 1
fi
dc "${COMPOSE_FILES[@]}" up -d --build

info "waiting for health (up to 150s)"
deadline=$(( $(date +%s) + 150 ))
while :; do
  unhealthy="$(dc "${COMPOSE_FILES[@]}" ps --format '{{.Name}} {{.Health}}' 2>/dev/null \
              | awk '$2 != "healthy" && $2 != "" {print $1}')"
  [ -z "$unhealthy" ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { warn "still not healthy: $unhealthy"; break; }
  sleep 3
done

ok "reset complete, town is back to golden state"
[ -n "${PKT_PACKS:-}" ] && echo "  active packs: $PKT_PACKS"
