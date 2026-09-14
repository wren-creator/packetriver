#!/usr/bin/env bash
# Shared helpers for the Packet River lifecycle scripts. Sourced, not run.
# Adapted from crosscreek/lib.sh.

if [ -t 1 ]; then
  C_RED=$'\033[31m'; C_GRN=$'\033[32m'; C_YEL=$'\033[33m'; C_BLU=$'\033[34m'; C_RST=$'\033[0m'
else
  C_RED=""; C_GRN=""; C_YEL=""; C_BLU=""; C_RST=""
fi

info() { printf '%s[*]%s %s\n' "$C_BLU" "$C_RST" "$*"; }
ok()   { printf '%s[+]%s %s\n' "$C_GRN" "$C_RST" "$*"; }
warn() { printf '%s[!]%s %s\n' "$C_YEL" "$C_RST" "$*"; }
bad()  { printf '%s[x]%s %s\n' "$C_RED" "$C_RST" "$*" >&2; }

# Resolve `docker compose` (v2) vs `docker-compose` (v1).
dc() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    bad "docker compose not found"; exit 1
  fi
}

require_docker() {
  command -v docker >/dev/null 2>&1 || { bad "docker not installed"; exit 1; }
  docker info >/dev/null 2>&1 || { bad "docker daemon not reachable"; exit 1; }
}

# Fail if the effective compose config publishes any port to a non-loopback
# host address. This is the guard that keeps a town full of deliberately
# vulnerable services, mini-sites, and soft-PLCs off the network. Packet River
# is reachable from the machine running it and nowhere else.
assert_loopback_only() {
  local cfg
  cfg="$(dc "$@" config 2>/dev/null)" || { bad "could not read compose config"; return 1; }
  local bad_binds
  bad_binds="$(printf '%s\n' "$cfg" | awk '
    /^[[:space:]]*-[[:space:]]*mode:[[:space:]]*ingress/ { ip="" }
    /^[[:space:]]*host_ip:/ { ip=$2; gsub(/"/,"",ip) }
    /^[[:space:]]*published:/ {
      pub=$2; gsub(/"/,"",pub)
      if (ip != "127.0.0.1") {
        print "  " (ip == "" ? "0.0.0.0(all interfaces)" : ip) ":" pub
      }
      ip=""
    }
  ')"
  if [ -n "${bad_binds//[[:space:]]/}" ]; then
    bad "refusing to continue: ports would bind beyond 127.0.0.1:"
    printf '%s\n' "$bad_binds" >&2
    return 1
  fi
  return 0
}

# --- Expansion packs -------------------------------------------------------
# Packs are self-contained add-ons dropped into packs/<name>/, never
# committed to this repo (see packs/README.md). PKT_PACKS is a
# comma-separated list of active pack names. start.sh sets it from repeated
# --pack <name> flags and persists it to ACTIVE_PACKS_FILE so stop.sh /
# reset.sh reconstruct the same file list without the user re-typing --pack
# on every lifecycle command.
ACTIVE_PACKS_FILE=".packetriver-active-packs"

save_active_packs() {
  if [ -n "${PKT_PACKS:-}" ]; then
    printf '%s\n' "$PKT_PACKS" > "$ACTIVE_PACKS_FILE"
  else
    rm -f "$ACTIVE_PACKS_FILE"
  fi
}

load_active_packs() {
  if [ -z "${PKT_PACKS:-}" ] && [ -f "$ACTIVE_PACKS_FILE" ]; then
    PKT_PACKS="$(cat "$ACTIVE_PACKS_FILE")"
  fi
}

# Build the -f file list for this invocation into the global array
# COMPOSE_FILES: base [+ base-segmented] [+ each active pack's compose file]
# [+ each active pack's segmented override]. Reads PKT_SEGMENTED=1 and
# PKT_PACKS="a,b,c" from env. Returns non-zero (with a bad() message) if a
# named pack isn't actually present under packs/.
compose_files() {
  COMPOSE_FILES=(-f docker-compose.yml)
  if [ "${PKT_SEGMENTED:-0}" = "1" ] && [ -f docker-compose.segmented.yml ]; then
    COMPOSE_FILES+=(-f docker-compose.segmented.yml)
  fi
  local name dir
  local IFS=','
  for name in ${PKT_PACKS:-}; do
    [ -z "$name" ] && continue
    dir="packs/$name"
    if [ ! -f "$dir/docker-compose.yml" ]; then
      bad "no such pack: $name (expected $dir/docker-compose.yml - see packs/README.md)"
      return 1
    fi
    COMPOSE_FILES+=(-f "$dir/docker-compose.yml")
    if [ "${PKT_SEGMENTED:-0}" = "1" ] && [ -f "$dir/docker-compose.segmented.yml" ]; then
      COMPOSE_FILES+=(-f "$dir/docker-compose.segmented.yml")
    fi
  done
  return 0
}
