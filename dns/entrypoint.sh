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

# --- reverse zone: resolve each container's it-net address now and write PTRs
# back to its primary public name. (Dynamic IPs, so this is a boot-time snapshot;
# a container restart would need a rebuild - noted in ROADMAP.)
REV=/etc/coredns/db.reverse
{
    printf '$ORIGIN 20.31.172.in-addr.arpa.\n$TTL 300\n'
    printf '@   IN  SOA ns.packetriver.range. hostmaster.packetriver.range. ( %s 3600 900 1209600 300 )\n' "$serial"
    printf '@   IN  NS  ns.packetriver.range.\n'
} > "$REV"

add_ptr() {                      # $1 = container name  $2 = public name
    ip="$(nslookup "$1" 127.0.0.11 2>/dev/null | awk '/^Address: /{print $2; exit}')"
    case "$ip" in
        172.31.20.*) printf '%s   IN  PTR  %s.\n' "${ip##*.}" "$2" >> "$REV" ;;
    esac
}
add_ptr packetriver-field-plc    water.packetriver.range
add_ptr packetriver-bank         firstpacketbank.packetriver.range
add_ptr packetriver-z16          core.firstpacketbank.packetriver.range
add_ptr packetriver-as400        payroll.packetriver.range
add_ptr packetriver-paygw        merchant.packetriver.range
add_ptr packetriver-traffic-plc  signals.packetriver.range
add_ptr packetriver-rail-plc     dispatch.packetriver.range
add_ptr packetriver-websites     townhall.packetriver.range
add_ptr packetriver-gateway      www.packetriver.range
add_ptr packetriver-scoring      scoring.packetriver.range
echo "[dns] reverse zone: $(grep -c 'IN  PTR' "$REV") PTR records"

# easter-egg hint (PKT_EGGS = subtle | obvious)
case "${PKT_EGGS:-off}" in
  subtle)  printf '_hint           IN  TXT     "the whole town is in this zone. all of it."\n' >> "$ZONE" ;;
  obvious) printf '_hint           IN  TXT     "this name server answers AXFR to anyone. dig axfr packetriver.range and read every line, not just the A records."\n' >> "$ZONE" ;;
esac

echo "[dns] zone built (serial ${serial}); AXFR is open on packetriver.range"

exec coredns -conf /etc/coredns/Corefile
