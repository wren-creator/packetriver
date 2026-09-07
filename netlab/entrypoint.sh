#!/bin/sh
set -eu

# segmented build: the guest network is WPA2-Enterprise-equivalent here, which
# we model as "the portal and mail are TLS now". Generate a self-signed cert
# so the MITM only ever sees ciphertext.
if [ "${NETLAB_TLS:-0}" = "1" ] && [ ! -f /app/tls.crt ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
        -subj "/CN=diner-wifi.packetriver.range" \
        -keyout /app/tls.key -out /app/tls.crt >/dev/null 2>&1
fi

if [ "${ROLE:-ap}" = "patron" ]; then
    exec python patron.py
fi
exec python ap.py
