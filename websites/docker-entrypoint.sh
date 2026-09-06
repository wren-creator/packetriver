#!/usr/bin/env bash
# Wait for the database, plant this session's flags where each bug reaches
# them, then start Apache (plus the barber "manager bot" loop). scoring writes
# each flag to /run/secret/<technique_id>/flag.txt.
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
q generalstore "DELETE FROM staff_notes; INSERT INTO staff_notes (note) VALUES ('$(flag generalstore_sqli)');" \
  && echo "[websites] planted generalstore"
q hardware "UPDATE receipts SET notes = 'contractor account audit key: $(flag hardware_idor)' WHERE customer='flag_holder';" \
  && echo "[websites] planted hardware"
q pharmacy "UPDATE patient_records SET note = 'records export token: $(flag pharmacy_authbypass)' WHERE patient='records audit';" \
  && echo "[websites] planted pharmacy"
q townhall "UPDATE announce_admin SET confirm_code = '$(flag townhall_deface)';" \
  && echo "[websites] planted townhall deface code"

# --- diner: a backup file left in the web root ---------------------------
cat > "$SITE/diner/db_backup.sql" <<SQL
-- The Daily Grind - nightly database dump (do not commit!)
-- ops flag: $(flag diner_backup)
CREATE TABLE users (id INT, username VARCHAR(64), password_hash CHAR(32));
INSERT INTO users VALUES (1,'manager','5f4dcc3b5aa765d61d8327deb882cf99');
SQL
chown www-data:www-data "$SITE/diner/db_backup.sql"
echo "[websites] planted diner backup"

# --- townhall: real payslips for the archive; the LFI target is the flag
#     file itself, reached by traversing out of the payslips directory --------
mkdir -p "$SITE/townhall/payslips"
for m in 2025-11 2025-12 2026-01; do
  printf 'PAYSLIP %s\nEmployee: P. Ellis\nGross: 3,120.00\nNet: 2,388.44\n' "$m" \
    > "$SITE/townhall/payslips/$m.txt"
done
chown -R www-data:www-data "$SITE/townhall/payslips"
echo "[websites] planted townhall payslips"

# --- police: an exposed dispatch config -------------------------------
mkdir -p "$SITE/police/dispatch"
cat > "$SITE/police/dispatch/config.json" <<JSON
{
  "cad_host": "dispatch.police.local",
  "repeater_channel": 4,
  "radio_key": "$(flag police_leak)",
  "note": "do not publish"
}
JSON
chown -R www-data:www-data "$SITE/police/dispatch"
echo "[websites] planted police dispatch config"

# --- fire: alarm panel key rendered from the flag file (see fire/index.php) ---

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
\$RECOVERY_KEY = '$(flag drycleaner_gitleak)';
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
