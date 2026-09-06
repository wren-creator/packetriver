#!/usr/bin/env bash
# Wait for the database, plant this session's flag inside it (read from the
# shared pkt-flags volume that scoring wrote), then start Apache.
set -uo pipefail

DB_HOST="${DB_HOST:-db}"
DB_NAME="${DB_NAME:-generalstore}"
DB_USER="${DB_USER:-shop}"
DB_PASS="${DB_PASS:-shop}"
FLAG_FILE="/run/secret/generalstore/flag.txt"

echo "[websites] waiting for ${DB_HOST}/${DB_NAME} ..."
for i in $(seq 1 60); do
  if mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "SELECT 1" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if [ -f "$FLAG_FILE" ]; then
  FLAG="$(head -n1 "$FLAG_FILE")"
  # single-quote-safe: the flag is [A-Za-z0-9_{}], no escaping needed
  mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" \
    -e "DELETE FROM staff_notes; INSERT INTO staff_notes (note) VALUES ('${FLAG}');" \
    && echo "[websites] General Store flag planted in staff_notes" \
    || echo "[websites] WARNING: could not plant flag"
else
  echo "[websites] WARNING: no flag at $FLAG_FILE (scoring not ready?)"
fi

exec "$@"
