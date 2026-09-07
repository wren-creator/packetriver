#!/usr/bin/env bash
# check-flags.sh - end-to-end smoke test of the mint -> plant -> submit -> score
# loop for every technique in the running flat range.
#
# It does NOT re-run the 24 exploits (that is Section B of
# docs/verification.md, driven by hand / the bundled scripts). It pulls the
# authoritative flag map straight out of scoring.db, then for each technique:
# arms it, submits the flag, and asserts the submission is accepted for at
# least the base points. A failure here means a flag was not planted, the
# scoring path is broken, or an effect key is wrong - not that an exploit
# regressed.
#
#   ./instructor/ctf/check-flags.sh            # against 127.0.0.1:8080
#   BASE_URL=http://127.0.0.1:8080 ./...       # override
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8080}"
JAR="$(mktemp)"
trap 'rm -f "$JAR"' EXIT
U="ctfcheck_$$_$RANDOM"
PW="checkPassw0rd123"
CT='Content-Type: application/json'
pass=0 fail=0

j() { python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get(sys.argv[1],""))' "$1"; }

echo "== check-flags :: $BASE_URL =="

# 1. the authoritative flag map from scoring.db
mapfile -t ROWS < <(docker compose exec -T scoring python -c '
import sqlite3
for tid, flag, base in sqlite3.connect("/data/scoring.db").execute(
        "SELECT technique_id, flag, base FROM flags ORDER BY technique_id"):
    print(f"{tid}\t{flag}\t{base}")
')
[ "${#ROWS[@]}" -gt 0 ] || { echo "!! no flags in scoring.db - is the range up?"; exit 2; }
echo "   ${#ROWS[@]} techniques in the flag map"

# 2. a throwaway account + run
curl -s -c "$JAR" -b "$JAR" -H "$CT" -d "{\"name\":\"$U\",\"password\":\"$PW\"}" \
     "$BASE_URL/api/score/register" >/dev/null
RID="$(curl -s -c "$JAR" -b "$JAR" -H "$CT" -X POST "$BASE_URL/api/score/run" | j run_id)"
[ -n "$RID" ] || { echo "!! could not start a run"; exit 2; }
echo "   run $RID as $U"
echo

# 3. arm + submit each flag
for row in "${ROWS[@]}"; do
    tid="${row%%$'\t'*}"; rest="${row#*$'\t'}"
    flag="${rest%%$'\t'*}"; base="${rest##*$'\t'}"

    # the flag file must have been planted on the shared volume
    if ! docker compose exec -T scoring sh -c "test -s /run/secret/$tid/flag.txt"; then
        printf '  %-22s FAIL  no /run/secret/%s/flag.txt\n' "$tid" "$tid"; fail=$((fail+1)); continue
    fi

    curl -s -c "$JAR" -b "$JAR" -H "$CT" -d "{\"technique_id\":\"$tid\"}" \
         "$BASE_URL/api/score/arm" >/dev/null
    resp="$(curl -s -c "$JAR" -b "$JAR" -H "$CT" -d "{\"flag\":\"$flag\"}" "$BASE_URL/api/score/submit")"
    accepted="$(printf '%s' "$resp" | j accepted)"
    points="$(printf '%s' "$resp" | j points)"

    if [ "$accepted" = "True" ] && [ "${points:-0}" -ge "$base" ]; then
        printf '  %-22s ok    %s pts (base %s)\n' "$tid" "$points" "$base"; pass=$((pass+1))
    else
        printf '  %-22s FAIL  %s\n' "$tid" "$resp"; fail=$((fail+1))
    fi
done

echo
echo "== $pass ok, $fail failed =="
[ "$fail" -eq 0 ]
