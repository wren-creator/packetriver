#!/bin/sh
# Build the live zone file (drop this run's dns_axfr flag into the stray
# TXT record, stamp a serial) and hand off to CoreDNS.
set -eu

TMPL=/etc/coredns/db.packetriver.range.tmpl
ZONE=/etc/coredns/db.packetriver.range
FLAG_FILE=/run/secret/dns_axfr/flag.txt

flag="PKTR{dns_axfr_not_provisioned}"
if [ -r "$FLAG_FILE" ]; then
    flag="$(tr -d '[:space:]' < "$FLAG_FILE")"
fi
serial="$(date +%Y%m%d%H)"

sed -e "s|@@FLAG@@|${flag}|g" -e "s|@@SERIAL@@|${serial}|g" "$TMPL" > "$ZONE"
echo "[dns] zone built (serial ${serial}); AXFR is open on packetriver.range"

exec coredns -conf /etc/coredns/Corefile
