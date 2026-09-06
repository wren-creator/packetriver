#!/usr/bin/env bash
# Wait for the database, plant this session's flags where each shop's bug
# reaches them, then start Apache (plus the barber "manager bot" loop).
set -uo pipefail

DB_HOST="${DB_HOST:-db}"
DB_USER="${DB_USER:-shop}"
DB_PASS="${DB_PASS:-shop}"
SEC=/run/secret
SITE=/var/www/site

flag() { head -n1 "$SEC/$1/flag.txt" 2>/dev/null || echo "flag-not-planted"; }
q()    { mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASS" "$1" -e "$2"; }

echo "[websites] waiting for the database ..."
for _ in $(seq 1 60); do
  mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASS" generalstore -e "SELECT 1" >/dev/null 2>&1 && break
  sleep 2
done

# --- flags that live in a DB row -------------------------------------------
q generalstore "DELETE FROM staff_notes; INSERT INTO staff_notes (note) VALUES ('$(flag generalstore)');" \
  && echo "[websites] planted generalstore"
q hardware "UPDATE receipts SET notes = 'contractor account audit key: $(flag hardware)' WHERE customer='flag_holder';" \
  && echo "[websites] planted hardware"
q pharmacy "UPDATE patient_records SET note = 'records export token: $(flag pharmacy)' WHERE patient='records audit';" \
  && echo "[websites] planted pharmacy"

# --- diner: a backup file left in the web root ---------------------------
cat > "$SITE/diner/db_backup.sql" <<SQL
-- The Daily Grind - nightly database dump (do not commit!)
-- ops flag: $(flag diner)
CREATE TABLE users (id INT, username VARCHAR(64), password_hash CHAR(32));
INSERT INTO users VALUES (1,'manager','5f4dcc3b5aa765d61d8327deb882cf99');
SQL
chown www-data:www-data "$SITE/diner/db_backup.sql"
echo "[websites] planted diner backup"

# --- drycleaner: a working git checkout in the web root ------------------
git config --global --add safe.directory '*'   # entrypoint runs as root; the tree is www-data
(
  cd "$SITE/drycleaner" || exit 0
  rm -rf .git
  git init -q
  git config user.email ops@drycleaner.local
  git config user.name ops
  cat > config.php <<PHP
<?php
\$DB_HOST = 'db';
\$DB_USER = 'shop';
\$DB_PASS = 'shop';
// TODO: move this out before go-live
\$RECOVERY_KEY = '$(flag drycleaner)';
PHP
  git add config.php index.php logout.php
  git commit -q -m "initial site import"
  sed -i "/RECOVERY_KEY/d" config.php
  git add config.php
  git commit -q -m "move recovery key to environment"
  chown -R www-data:www-data .git config.php
)
echo "[websites] planted drycleaner .git"

# --- barber: the manager-review bot -------------------------------------
export BARBER_MGR_TOKEN="$(cat /proc/sys/kernel/random/uuid)"
(
  sleep 5
  while true; do
    curl -s "http://localhost/barber/review.php?token=${BARBER_MGR_TOKEN}" >/dev/null 2>&1
    sleep 4
  done
) &
echo "[websites] barber manager bot running"

exec "$@"
