# player: the boxed-in attacker workstation. Real open-source tools, no route
# off the lab. Attack the town from here, or set PKT_LIGHT=1 and use your own
# shell against the published ports instead.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      sqlmap nmap curl jq iproute2 ca-certificates less \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pymodbus==3.6.9

COPY scripts/ /opt/pktr/scripts/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /opt/pktr/scripts/*.sh 2>/dev/null || true

WORKDIR /opt/pktr
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
