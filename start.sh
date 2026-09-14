#!/usr/bin/env bash
# Bring Packet River up. Refuses to launch if any published port would bind
# beyond 127.0.0.1.
#   --segmented        start with the hardened topology (every weakness off)
#                       instead of the flat, vulnerable-by-default town
#   --pack <name>       layer in an expansion pack from packs/<name>/ (repeat
#                       for more than one; see packs/README.md)
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

PKT_SEGMENTED=0
PKT_PACKS=""
MODE="flat (vulnerable defaults)"
while [ $# -gt 0 ]; do
  case "$1" in
    --segmented)
      PKT_SEGMENTED=1
      MODE="segmented (hardened)"
      info "segmented topology selected"
      shift
      ;;
    --pack)
      [ -n "${2:-}" ] || { bad "--pack needs a name"; exit 1; }
      PKT_PACKS="${PKT_PACKS:+$PKT_PACKS,}$2"
      shift 2
      ;;
    *)
      bad "unknown argument: $1"
      exit 1
      ;;
  esac
done
export PKT_SEGMENTED PKT_PACKS

if [ "$PKT_SEGMENTED" = "1" ] && [ ! -f docker-compose.segmented.yml ]; then
  warn "docker-compose.segmented.yml not present yet (arrives in Phase 4), starting flat"
  PKT_SEGMENTED=0
  MODE="flat (vulnerable defaults)"
fi

require_docker

if ! compose_files; then
  exit 1
fi
[ -n "$PKT_PACKS" ] && info "active packs: $PKT_PACKS"

info "loopback-only guard"
if ! assert_loopback_only "${COMPOSE_FILES[@]}"; then
  bad "not starting"
  exit 1
fi
ok "all published ports bind to 127.0.0.1"

save_active_packs

info "starting containers"
dc "${COMPOSE_FILES[@]}" up -d

info "waiting for health (up to 150s)"
deadline=$(( $(date +%s) + 150 ))
while :; do
  unhealthy="$(dc "${COMPOSE_FILES[@]}" ps --format '{{.Name}} {{.Health}}' 2>/dev/null \
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
[ -n "$PKT_PACKS" ] && echo "  active packs:           $PKT_PACKS"
echo "  city map        http://127.0.0.1:8080/"
echo "  General Store   http://127.0.0.1:8090/   (a target - click it on the map too)"
echo "  field HMI       http://127.0.0.1:8093/   (water + power operator screen, operator/operator)"
echo "  water Modbus    127.0.0.1:5502   /  power Modbus  127.0.0.1:5503   (no auth)"
echo "  event bus       127.0.0.1:1883   MQTT (also a target: pkt/traffic/#)"
echo
echo "  attacker shell:         docker compose exec player sh"
echo "  reset to golden state:  ./reset.sh"
echo "  hardened run:           ./start.sh --segmented   (Phase 4+)"
echo "  add an expansion pack:  ./start.sh --pack <name>   (see packs/README.md)"
