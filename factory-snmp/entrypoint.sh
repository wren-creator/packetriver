#!/bin/sh
set -eu

CONF=/etc/snmp/snmpd.conf
if [ "${SNMP_HARDENED:-0}" = "1" ]; then
    # segmented build: no write community, and the read community is not `public`
    sed -i \
        -e 's/^rwcommunity .*/# rwcommunity removed (hardened)/' \
        -e "s/^rocommunity public/rocommunity ${SNMP_RO_COMMUNITY:-pkw-ro-8831}/" \
        "$CONF"
fi

# snmpd wants to background; -f keeps it in the foreground for the container
exec snmpd -f -Lo -C -c "$CONF"
