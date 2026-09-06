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

# Which compose files make up the current invocation. Defaults to the flat
# town; callers pass --segmented to fold in the hardened override.
compose_files() {
  local args=(-f docker-compose.yml)
  if [ "${PKT_SEGMENTED:-0}" = "1" ]; then
    args+=(-f docker-compose.segmented.yml)
  fi
  printf '%s\n' "${args[@]}"
}
