#!/usr/bin/env bash
# Health, reachability, the loopback bind audit, and a containment check that
# the player box (once it exists) has no route off the lab and cannot reach
# the OT segment without pivoting.
set -uo pipefail
cd "$(dirname "$0")"
source ./lib.sh

PIVOT_GAP=0

require_docker

FILES=(-f docker-compose.yml)
if dc -f docker-compose.yml -f docker-compose.segmented.yml ps --format '{{.Name}}' 2>/dev/null \
     | grep -q packetriver-ids; then
  FILES+=(-f docker-compose.segmented.yml)
fi

info "containers"
dc "${FILES[@]}" ps

echo
info "endpoint checks"
code="$(curl -fsS -o /dev/null -w '%{http_code}' "http://127.0.0.1:8080/health" 2>/dev/null || true)"
[ "$code" = "200" ] && ok "city map  ($code)" || bad "city map  ($code)"
gs="$(curl -fsS -o /dev/null -w '%{http_code}' "http://127.0.0.1:8090/health.php" 2>/dev/null || true)"
if [ "$gs" = "200" ]; then ok "General Store  ($gs)"
elif [ -z "$gs" ] || [ "$gs" = "000" ]; then warn "General Store  (not running)"
else bad "General Store  ($gs)"; fi
if (exec 3<>"/dev/tcp/127.0.0.1/1883") 2>/dev/null; then ok "event bus  (127.0.0.1:1883 open)"; exec 3>&- || true
else bad "event bus  (127.0.0.1:1883 closed)"; fi

echo
info "loopback bind audit"
AUDIT_FAIL=0
while read -r name ports; do
  [ -z "$ports" ] && continue
  if printf '%s' "$ports" | grep -Eq '(^|[, ])0\.0\.0\.0:|(^|[, ])\[?::\]?:|(^|[, ])\*:'; then
    bad "$name exposes a non-loopback binding: $ports"
    AUDIT_FAIL=1
  else
    ok "$name  $ports"
  fi
done < <(dc "${FILES[@]}" ps --format '{{.Name}}\t{{.Ports}}' 2>/dev/null)

echo
info "containment: player box must not reach the internet, nor the OT segment directly"
if dc "${FILES[@]}" ps --format '{{.Name}}' 2>/dev/null | grep -q packetriver-player; then
  if dc "${FILES[@]}" exec -T player python3 -c \
       'import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(("1.1.1.1",53)) == 0)' \
       2>/dev/null; then
    ok "player container cannot reach the internet"
  else
    bad "player container reached a public address, stop the town"
    AUDIT_FAIL=1
  fi
  # The player has no business reaching the PLC status port before a pivot. Same
  # exit-code convention as the internet check above: connect_ex()==0 on a
  # successful connect -> sys.exit(True) -> rc 1 -> the shell `if` is false ->
  # the `else` (bad/warn) branch. A failed connect -> rc 0 -> the `ok` branch.
  # NOTE: there is no ot-net yet, so today this warns rather than fails - the
  # player shares it-net with traffic-plc. Tracked in ROADMAP.md ("real OT
  # segmentation"); docs/verification.md A1 expects this one warn line.
  if dc "${FILES[@]}" ps --format '{{.Name}}' 2>/dev/null | grep -q packetriver-traffic-plc; then
    if dc "${FILES[@]}" exec -T player python3 -c \
         'import socket,sys; s=socket.socket(); s.settimeout(3); sys.exit(s.connect_ex(("traffic-plc",8095)) == 0)' \
         2>/dev/null; then
      ok "player cannot reach the OT segment without pivoting"
    else
      warn "player can reach traffic-plc:8095 directly - known Phase-4 gap, no ot-net yet (see ROADMAP.md)"
      PIVOT_GAP=1
    fi
  fi
else
  warn "player container not running (arrives in Phase 1), skipped"
fi

echo
if [ "$AUDIT_FAIL" -ne 0 ]; then
  bad "audit FAILED: something is reachable it should not be, stop the town"
elif [ "$PIVOT_GAP" -ne 0 ]; then
  ok "audit clean: town is loopback-only, no internet from the player box"
  warn "1 known gap: no ot-net yet, so the player reaches the PLCs without a pivot (ROADMAP.md)"
else
  ok "audit clean: town is loopback-only and the player box is boxed in"
fi

[ "$AUDIT_FAIL" -eq 0 ] || exit 1
