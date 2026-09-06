#!/usr/bin/env bash
# Bring Packet River up. Refuses to launch if any published port would bind
# beyond 127.0.0.1.
#   --segmented   start with the hardened topology (every weakness off) instead
#                 of the flat, vulnerable-by-default town
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

COMPOSE_ARGS=(-f docker-compose.yml)
MODE="flat (vulnerable defaults)"
if [ "${1:-}" = "--segmented" ]; then
  if [ -f docker-compose.segmented.yml ]; then
    COMPOSE_ARGS+=(-f docker-compose.segmented.yml)
    MODE="segmented (hardened)"
    info "segmented topology selected"
  else
    warn "docker-compose.segmented.yml not present yet (arrives in Phase 4), starting flat"
  fi
fi

require_docker

info "loopback-only guard"
if ! assert_loopback_only "${COMPOSE_ARGS[@]}"; then
  bad "not starting"
  exit 1
fi
ok "all published ports bind to 127.0.0.1"

info "starting containers"
dc "${COMPOSE_ARGS[@]}" up -d

info "waiting for health (up to 150s)"
deadline=$(( $(date +%s) + 150 ))
while :; do
  unhealthy="$(dc "${COMPOSE_ARGS[@]}" ps --format '{{.Name}} {{.Health}}' 2>/dev/null \
              | awk '$2 != "healthy" && $2 != "" {print $1}')"
  [ -z "$unhealthy" ] && break
  if [ "$(date +%s)" -ge "$deadline" ]; then
    warn "still not healthy: $unhealthy"
    warn "check: ./status.sh  and  docker compose logs"
    break
  fi
  sleep 3
done

echo
ok "Packet River is up  [$MODE]"
echo "  city map        http://127.0.0.1:8080/"
echo "  General Store   http://127.0.0.1:8090/   (a target - click it on the map too)"
echo "  event bus       127.0.0.1:1883   MQTT (also a target: pkt/traffic/#)"
echo
echo "  attacker shell:         docker compose exec player sh"
echo "  reset to golden state:  ./reset.sh"
echo "  hardened run:           ./start.sh --segmented   (Phase 4+)"
